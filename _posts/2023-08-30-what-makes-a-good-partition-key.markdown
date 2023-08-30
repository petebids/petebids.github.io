---
layout: post
title:  "How to distribute load effectively on Apache Kafka using partition keys"
date:   2023-08-30 
categories:  Distributed Systems, Kafka, Partitioning
---

## Abstract

In this article, I'll walk through one of the building blocks of the design & development of a highly performant event stream on Apache Kafka. 
I'll skip details around event design, dead-letter queues, log compaction, data serialisation, security, & schema evolution that would 
all work in conjunction with this choice in a production system,
so we can deep dive into the process for selecting a partition strategy, a partition or message key, and then verifying that your choice has the expected distribution.

## Understanding topic partitions in Kafka


![Diagram](/assets/topic.png)

The key to understanding topic partitions in Kafka is the idea that they are logically contiguous, but physically separate.

What this means is that if we have a topic of Orders  - each partition contains a non-overlapping subset of orders 

These partitions will be seperated across different brokers in a Kafka cluster. These partitions form the unit of concurrency - the more partitions, the more consumers we can attach,
& the greater throughput our system can achieve - **assuming an even distribution**

We can write an application where we code in the abstract for the most part - thinking about a stream of objects, shared via Kafka
Under the hood, the kafka protocol will ensure ordered delivery within those partitions.


## The tradeoff at play


So the benefit of partitions is that they are physically separate - meaning less resource contention, higher rates of parallelization
The cost is that there is no coordination of data between them - meaning no guarantee of ordering <b>across</b> partitions - only <b>within</b> them. 

This means that a partition is a hard boundary on the ordered delivery guarantee Kafka provides.

## Our imaginary scenario

Let's just say we are some kind of ecommerce system that takes orders from customers.
When an order goes through its lifecycle, the status changes, & an event is emitted via Kafka.
The comms system subscribes to these events, & sends customers emails.

![Diagram](/assets/arch.png)


Let's assume that the comms team has a good handle on how they will that process  the events in an idempotent, safe, secure manner,
& all they need is a reasonable guarantee around the order messages will arrive in. 


## The design question -- Do I need to leverage ordering within kafka? 

This is a fundamental property of any event stream - how does order of events factor into the way consumers will read them ?

In our over simplified scenario, lets assume orders can change state in the following ways 

- When an order is created, it goes on back order
- When stock is available, an order is shipped
- When the shipping is complete the order is marked as completed

Let's just say in our scenario, the design choice is made that the comms engine shouldn't need to know about the cause & effect relationship between our events - it should just be able to process them in order & turn them into emails.

Let's also rule out two other options for the purpose of this discussion. 

- Lamport or Vector clocks - a logical clock that expresses to a consumer that event a happens before event b, without relying on the transport mechanism to keep messages. 
  - while this is a brilliant option to increase scalability & distribution of data, it forces consumers to implement the event buffer pattern, where if event b arrives before event a, they have to hold & process b until a arrives.
- A monolog architecture, where absolute ordering is guaranteed
  - A monolog assumes absolute ordering at a source of truth system. This rules out a lot of architectural choices that might help scaling in the source-of-truth database, & would only allow us to use a single partition on kafka, dramatically limiting our throughput


For our purposes, let's assume we need to deliver order events **in order** to the service that publishes email communications, & that we will use Kafka Partitions to guarantee this order.

So we can compromise on limited ordering guarantee - updates for any given order will arrive in order, relative to other updates for the same order
this means we won't tell a customer that their order has shipped after it's been delivered



## Ok - I think I've picked a good key - how do I test it ?

You could of course just go ahead and publish directly to Kafka & see the results. 

For a meaningfully sized data set, this might take hours or days - not mention the fact you have to get your publishing code in a decent state.

One option I've developed this year is the following mechanism of left-shifting partition distribution - if you find a partition key is unsuitable, you can pivot early, 

First of all - we find out [how Kafka calculates partitions by key](https://github.com/apache/kafka/blob/660e6fe8108e8a9b3481ea1ec20327a099dd8310/clients/src/main/java/org/apache/kafka/clients/producer/KafkaProducer.java#L1403)


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
And then some code to generate a Mock topic. 

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

- population isn't normally distributed between countries
- employees aren't  between companies



```java


    @DisplayName("A slightly improved partition key")
    @Test
    void slightImprovement() {

        MockOrderFactory mockOrderFactory = getMockOrderFactory();
        Stack<Order> orders = mockOrderFactory.generateWeightedOrders(1_000_000);

        MockKafkaTopic mockKafkaTopic = MockTopicGenerator
        .mockTopic(() -> orders.pop().customerId().toString(), 10, 1_000_000);

        Map<Integer, Integer> summary = mockKafkaTopic.getSummary();



        assertThat(summary.get(0), allOf(greaterThan(45_000), lessThan(65_000)));
        assertThat(summary.get(1), allOf(greaterThan(145_000), lessThan(160_000)));
        assertThat(summary.get(2), allOf(greaterThan(85_000), lessThan(100_000)));
        assertThat(summary.get(3), allOf(greaterThan(38_000), lessThan(45_000)));
        assertThat(summary.get(4), allOf(greaterThan(110_00), lessThan(130_000)));
        assertThat(summary.get(5), allOf(greaterThan(130_000), lessThan(180_000)));
        assertThat(summary.get(6), allOf(greaterThan(55_000), lessThan(65_000)));
        assertThat(summary.get(7), allOf(greaterThan(90_000), lessThan(115_000)));
        assertThat(summary.get(8), allOf(greaterThan(120_000), lessThan(150_000)));
        assertThat(summary.get(9), allOf(greaterThan(85_000), lessThan(100_000)));



        }

```

![Diagram](/assets/partition_by_customer.png)



### An ideal choice 

So even with a randomly generated Customer id - we still ended up with skewed partitions 

That means, we don't need to take into account the other biases in our system - the skew towards Pickup or delivery orders, or the fact some customers might be more active than others
 
assuming that - on average,orders go through a normal lifecycle, & produce a normal amount of state changes - we might get something like this


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


# Tying it all together - Which tradeoff is right for us?

Let's assume we can rule out partitioning by type & status - status wouldn't guarantee ordering at all, ordering by type wouldn't make effective use of partitions

That leaves us with ordering by customer id, or order id

If we partition by customer id 

- we won't get an optimally even distribution
- If customers have multiple orders in flight, every update they get will be in perfect order 


If we partition by order id

- We are more likely to end up with an even distribution over time
- If customers have multiple orders in flight, they might receive notifications for **separate** orders,  out of order

This sounds like something we might want to guard against, but equally this could be something outside the scope of our system - 
we might not have a guarantee from our suppliers that orders for different products will be filled sequentially.

In that case, we don't lose anything by partitioning on the order id. 



# Summary


Thanks for getting this far
In this article, we've taken one path down a decision tree for a distributed architecture & looked at how it can be optimised.
In reality, a lot of the assumptions we've made today are worth being challenged - opening up different possibilities.

I hope you've gained an appreciation for the technical challenges that go into leveraging the power of a distributed system like Kafka, 
while maintaining a balance between competing business & technical requirements, as well as an appreciation for seemingly minor semantic differences
that can manifest as technical debt over time.

I've included some rough [source code](https://github.com/petebids/kafka-partition-test/tree/main) that made up the bulk of this article to help get you started, 
should you want to apply the shift left method of testing partition strategies.

Thanks for reading!







