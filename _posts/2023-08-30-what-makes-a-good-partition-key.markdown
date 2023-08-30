---
layout: post
title:  "How to distribute load effectively on Apache Kafka ?"
date:   2023-08-30 
categories:  Distributed Systems, Kafka, Partitioning
---

## Abstract

In this article, I'll walk through one of the building blocks of the design & development of a highly performant event stream on Apache Kafka. 
I'll skim over details around event design, data serialisation, security, & schema evolution,
so we can deep dive into the process for selecting a partition strategy, a partition or message key, and then verifying that 

## Understanding topic partitions in Kafka

The key to understanding topic partitions in Kafka is the idea that they are logically contiguous, but physically separate

What this means is that if we have a topic of Orders - each partition contains a non-overlapping subset of orders 

These partitions will be seperated across different brokers in a Kafka cluster. 

We can write an application where we code in the abstract for the most part - thinking about a stream of business objects, shared via Kafka


## The tradeoff at play


So the benefit of partitions is that they are physically separate - meaning less resource contention, higher rates of parallelization
The cost is that there is no coordination of data between them - meaning no guarantee of ordering across partitions - only within them! 



## The design question -- Do I need to leverage ordering within kafka? 

This is a fundamental property of any event stream - how does order of events factor into the way consumers will read them ? 
This is a great time to remember that just because a message queue or streaming technology offers a feature, doesn't mean you should use it! 

Consider Lamport or Vector clocks - the ordering can be embedded into the message
Consumers can buffer for the next event, due to the specific happens after semantics

You still want to use kafka for ordering ? 


ok - You still want to use kafka ordering ?  what are the acceptable bounds of ordering ? 



## Ok - I think I;ve picked a good key - how do I test it ? 

Fundamentally - we can think of a Kafka topic as a two-dimensional list 
 the outer list contain the partitions, and the partitions contain the messages

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














