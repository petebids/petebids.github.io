---
layout: post
title:  "How to distribute load effectively on Apache Kafka using partition keys"
date:   2023-08-30 
categories:  Distributed Systems, Kafka, Partitioning
---

## Abstract

In this article, I'll walk through one of the building blocks of the design & development of a highly performant event stream on Apache Kafka. 
I'll skim over details around event design, data serialisation, security, & schema evolution,
so we can deep dive into the process for selecting a partition strategy, a partition or message key, and then verifying that your choice has the expected distribution

## Understanding topic partitions in Kafka


![Diagram](/assets/topic.png)

The key to understanding topic partitions in Kafka is the idea that they are logically contiguous, but physically separate

What this means is that if we have a topic of Orders - each partition contains a non-overlapping subset of orders 

These partitions will be seperated across different brokers in a Kafka cluster. These partitions form the unit of concurrency - the more partitions, the more consumers we can attach,
& the greater throughput our system can achieve - **assuming an even distribution**

We can write an application where we code in the abstract for the most part - thinking about a stream of business objects, shared via Kafka
Under the hood, the kafka protocol will ensure ordered delivery within those partitions


## The tradeoff at play


So the benefit of partitions is that they are physically separate - meaning less resource contention, higher rates of parallelization
The cost is that there is no coordination of data between them - meaning no guarantee of ordering <b>across</b> partitions - only <b>within</b> them! 

## Our imaginary scenario

Let's just say we are a system that produces events about orders. 

We know we want this information to be used in multiple places, but a key one is sending email comms to customers about thier order & it's state

Let's assume that team has a good handle on how they will that process idempotent, & all they need is a reasonable guarentee around the order messages will arrive in
TODO doc

## The design question -- Do I need to leverage ordering within kafka? 

This is a fundamental property of any event stream - how does order of events factor into the way consumers will read them ? 
This is a great time to remember that just because a message queue or streaming technology offers a feature, doesn't mean you should use it! 

As an example, if you were building something that aggregated application logs, & absolute order was never a requirement
Consider Lamport or Vector clocks - the ordering can be embedded into the message
Consumers can buffer for the next event, due to the specific happens after semantics

For our purposes, let's rule this out & assume we need to deliver order events to the service that publishes email communications.
Ideally orders would arrive in the order that they happen, but let's assume our order volume is too high to use a single partition, 

so we can compromise on limited ordering guarantee - updates for any given order will arrive in order, relative to other updates for the same order
this means we won't tell a customer that their order has shipped after it's been delivered



## Ok - I think I've picked a good key - how do I test it ?

You could of course just go ahead and publish directly to Kafka & see the results. 

For a meaningfully sized data set, this might take hours or days - not mention the fact you have to get your publishing code in a decent state.

One option I've developed this year is the following mechanism of left-shifting partition distribution - if you find a partition key is unsuitable, you can pivot early, 

First of all - we find out how Kafka Calculates partitions by key

https://github.com/apache/kafka/blob/660e6fe8108e8a9b3481ea1ec20327a099dd8310/clients/src/main/java/org/apache/kafka/clients/producer/KafkaProducer.java#L1403


Fundamentally - we can think of a Kafka topic as a two-dimensional array
the outer arraylist contain the partitions, and the partitions contain the messages

So a reasonable Mock for testing purposes is
```java
public class MockKafkaTopic {

    private final ArrayList<ArrayList<String>> data;


    public MockKafkaTopic(int partitions) {
        data = new ArrayList<>();
        for (int i = 0; i < partitions ; i++) {
            data.add(new ArrayList<>());
        }
    }


    public void publishToPartition(int partition, String key) {

        data.get(partition).add(key);
    }


    public  Map<Integer, Integer> getSummary() {

        Map<Integer, Integer> summary = new HashMap<>();
        for (int i = 0; i < data.size(); i++) {
            summary.put(i, data.get(i).size());

        }

        return summary;
    }
}

```
And then some code to generate a Mock topic

```java
public class MockTopicGenerator {
    
    public static MockKafkaTopic mockTopic(Supplier<String> partitionKeySupplier, int partitionCount, int iterations) {

        MockKafkaTopic mockKafkaTopic = new MockKafkaTopic(partitionCount);

        IntStream.range(0, iterations )
                .forEach(unused -> {
                    String partitionKey = partitionKeySupplier.get();
                    int i = BuiltInPartitioner.partitionForKey(partitionKey.getBytes(StandardCharsets.UTF_8), partitionCount);
                    mockKafkaTopic.publishToPartition(i, partitionKey);
                });

        return mockKafkaTopic;
    }

}

```

From here, we need realistic inputs. For a production system already running that it about to start publishing data, we don't need to mock - the `partitionKeySupplier`
should source real data from production. If we don't have a realistic dataset to use, we can brainstorm with a product manager about how we expect the system to be used, & produce some mock data as I've done throughout the repository



### A poor choice - order type
if we assume that orders cant change type, from Pickup to Delivery - then
 - an order of a type t will always return hash h / partition count pc which will always equal partition p 

great - we've found a stable key - all future versions of the same order will land on the same partition. 

Let's see how this pans out 

```java
    @DisplayName("A poor choice of partition key")
    @Test
    void poorPartitionKey() {

        MockOrderFactory mockOrderFactory = getMockOrderFactory();

        Stack<Order> orders = mockOrderFactory.generateWeightedOrders(1_000_000);

        MockKafkaTopic mockKafkaTopic = MockTopicGenerator
                .mockTopic(() -> orders.pop().type().toString(), 10, 1_000_000);

        Map<Integer, Integer> summary = mockKafkaTopic.getSummary();


        assertEquals(summary.get(0), 0);
        assertEquals(summary.get(1), 0);
        assertEquals(summary.get(2), 0);
        assertEquals(summary.get(3), 0);
        assertEquals(summary.get(4), 0);
        assertEquals(summary.get(5), 0);
        assertThat(summary.get(6), allOf(greaterThan(200_000), lessThan(300_000)));
        assertEquals(summary.get(7), 0);
        assertEquals(summary.get(8), 0);
        assertThat(summary.get(9), allOf(greaterThan(700_000), lessThan(800_000)));

    }


```

![Diagram](/assets/partition_by_order_type.png)

Well yes we have - but not a good one for the purpose of evenly distributing load!

There are only two states - meaning only two partitions receive messages. This is a poor partition key



### A Better choice - customer id 



This might work really well if your customer's behaviour has a normal distribution.  

In this example I've weighted customer's ordering behaviour to be a bit biased - not every customer places the same amount of orders

This a relatively common theme in the intersection of tech & human behaviour 

- population isn't normally distributed between countries
- employees aren't  between companies
- 


```java


    @DisplayName("A slightly improved partition key")
    @Test
    void slightImprovement() {

        MockOrderFactory mockOrderFactory = getMockOrderFactory();

        Stack<Order> orders = mockOrderFactory.generateWeightedOrders(1_000_000);

        MockKafkaTopic mockKafkaTopic = MockTopicGenerator
                .mockTopic(() -> orders.pop().customerId().toString(), 10, 1_000_000);

        Map<Integer, Integer> summary = mockKafkaTopic.getSummary();
        

        assertThat(summary.get(0), allOf(greaterThan(70_000), lessThan(80_000)));
        assertThat(summary.get(1), allOf(greaterThan(130_000), lessThan(140_000)));
        assertThat(summary.get(2), allOf(greaterThan(70_000), lessThan(80_000)));
        assertThat(summary.get(3), allOf(greaterThan(30_000), lessThan(40_000)));
        assertThat(summary.get(4), allOf(greaterThan(60_000), lessThan(80_000)));
        assertThat(summary.get(5), allOf(greaterThan(130_000), lessThan(180_000)));
        assertThat(summary.get(6), allOf(greaterThan(150_000), lessThan(200_000)));
        assertThat(summary.get(7), allOf(greaterThan(55_000), lessThan(85_000)));
        assertThat(summary.get(8), allOf(greaterThan(70_000), lessThan(80_000)));
        assertThat(summary.get(9), allOf(greaterThan(130_000), lessThan(140_000)));


```

![Diagram](/assets/partition_by_customer.png)



### An ideal choice 

So even with a randomly generated Customer id - we still ended up with skewed partitions 

That means, we don't need to take into account the other biases in our system - the skew towards Pickup or delivery orders, or the fact some customers might be more active than others
 
assuming that - on average,orders go through a normal lifecycle, & produce a normal amount of state changes 


```java

@DisplayName("An ideal partition Key")
@Test
    void idealKey() {


        MockOrderFactory mockOrderFactory = getMockOrderFactory();

        Stack<Order> orders = mockOrderFactory.generateWeightedOrders(1_000_000);

        MockKafkaTopic mockKafkaTopic = MockTopicGenerator
        .mockTopic(() -> orders.pop().orderId().toString(), 10, 1_000_000);

        Map<Integer, Integer> summary = mockKafkaTopic.getSummary();


        

        assertThat(summary.get(0), allOf(greaterThan(99_000), lessThan(101_000)));
        assertThat(summary.get(1), allOf(greaterThan(99_000), lessThan(101_000)));
        assertThat(summary.get(2), allOf(greaterThan(99_000), lessThan(101_000)));
        assertThat(summary.get(3), allOf(greaterThan(99_000), lessThan(101_000)));
        assertThat(summary.get(4), allOf(greaterThan(99_000), lessThan(101_000)));
        assertThat(summary.get(5), allOf(greaterThan(99_000), lessThan(101_000)));
        assertThat(summary.get(6), allOf(greaterThan(99_000), lessThan(101_000)));
        assertThat(summary.get(7), allOf(greaterThan(99_000), lessThan(101_000)));
        assertThat(summary.get(8), allOf(greaterThan(99_000), lessThan(101_000)));
        assertThat(summary.get(9), allOf(greaterThan(99_000), lessThan(101_000)));

        }

```


![Diagram](/assets/partition_by_order.png)




## other effective ways to distribute load

### Round robin partitioning & Vector clocks






