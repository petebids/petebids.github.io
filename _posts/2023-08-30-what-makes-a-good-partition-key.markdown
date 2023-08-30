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

Consider Lamport or Vector clocks - the ordering can be embedded into the message
Consumers can buffer for the next event, due to the specific happens after semantics

For our purposes, let's rule this out & assume we need to deliver order events to the service that publishes email communications.
Ideally orders would arrive in the order that they happen, but let's assume our order volume is too high to use a single partition, 

so we can compromise on limited ordering guarantee - updates for any given order will arrive in order, relative to other updates for the same order
this means we won't tell a customer that their order has shipped after it's been delivered

TODO doc order state machine 


### a poor choice - order type
if we assume that orders cant change type, from Pickup to Delivery - then
 - an order of a type t will always return hash h / partition count pc which will always equal partition p 

great - we've found a stable key - right ? 

TODO doc


Well yes we have - but not a good one for the purpose of evenly distributing load

there are only two states - 




### a Better choice - customer id 



this might work really well if your customer's behaviour has a normal distribution.  

In this example I've weighted customer's ordering behaviour to be a bit biased 


### An ideal choice 

in the aggregate, V4 UUIDs are truly random

that means, we don't need to take into account the other biases in our system - the skew towards Pickup or delivery orders, or the fact some customers might be more active than others
 
assuming that - on average, orders go through a normal lifecycle,  & produce a normal 


## Ok - I think I;ve picked a good key - how do I test it ? 

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











## other effective ways to distribute load

### Round robin paritioning & Vector clocks






