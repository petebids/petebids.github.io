---
layout: post
title:  "Spring Boot & the Transactional Outbox pattern"
date:   2023-03-12 14:52:29 +1100
categories: spring boot, kafka, postgres
---
# What is it?

The transactional outbox is an abstract pattern whereby backend engineers write code that combines internal state changes & the intent to publish corresponding events in one database transaction. State changes will be persisted to thier usual tables, & events to out outbox. Some other process then assumes responsibility for publishing the events from the outbox to the message store.

![Diagram](/assets/transactional_outbox.png)

See 
- the [brilliant technology agnostic explination](https://microservices.io/patterns/data/transactional-outbox.html)  & from Chris Richardson 
- fantastic [Quarkus Event Router implementation ](https://debezium.io/documentation/reference/stable/integrations/outbox.html) by Gunnar Morling




# When would I use this pattern?
- you want to publish events related to changes in data in your service
- You want transactional guarantees* around internal stage changes & event publication
- You want a runtime guarantee that your messages can be read by the consumer
- you want read your own writes semantics
- Throughput from web request to Kafka is not the highest priority





# When should I not use this pattern? 

- In an application without a strong business layer, where lots of database writes happen in external processes
  - The idea here is we are providing events based on changes ! if we have untracked changes, we can't guarentee the publishing of changes
- If you are using a database that doesn't support transactions across tables like GCP datastore or pre-accord Apache Cassandra; 



# Why can't i just ... 

- publish to kafka in a @Transactional method?
  - we have to use 2 phase commit
  - we introduce complexity into use of multiple transaction managers
  - we have lowered our uptime - If Kafka is unvailable, so is our service
- write to kafka only & do DB updates later
  - can't read you own writes
  - introduces complexity around consistency 
- use Kafka connect directly on tables ? 
  - lose the schema guarantees






# Ok - so how does it work ?

Technically speaking - this is a producer instead of a polling producer given the use of the Postgres connector instead of a JDBC connector - while this is semantically correct, as a "black box"

## Transactional Guarantee
  

  
  
## Schema Evolution Guarantee





## Credit to

In tech, we stand on the shoulder of giants. A heartfelt thanks to the work of the following individuals for thier brilliant work than enabled this article.

 - Chris Richardson
 - Gunnar Morling

