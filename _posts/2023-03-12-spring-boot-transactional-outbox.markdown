---
layout: post
title:  "Spring Boot & the Transactional Outbox pattern"
date:   2023-03-12 14:52:29 +1100
categories: spring boot, kafka, postgres
---

![Diagram](/assets/transactional_outbox.png)


# What is it?

The transactional outbox is an abstract pattern whereby backend engineers write code that combines internal state changes & the intent to publish corresponding events in one database transaction. State changes will be persisted to thier usual tables, & events to out outbox. Some other process then assumes responsibility for publishing the events from the outbox to the message store. In this example, we will look at an example that uses a Spring Boot RESTful API, Postgress Database for storage, Kafka Connect for log tailing and Kafka as a distributed event log



![Sequence](/assets/outbox_sequence.png)




See 
- the [brilliant technology agnostic explination](https://microservices.io/patterns/data/transactional-outbox.html)  & from Chris Richardson 
- fantastic [Quarkus Event Router implementation ](https://debezium.io/documentation/reference/stable/integrations/outbox.html) by Gunnar Morling
- my [example implementation](https://github.com/petebids/todo-tx-outbox)


# The Implementation 
 
Let's quickly go through the key points of the solution 
- The Service layer

```java


    @SneakyThrows
    public Todo create(NewTodoCommand command) {

        final Supplier<Todo> todoEntitySupplier = () -> {

            final UserEntity creator = userRepository.findById(UUID.fromString(command.creator()))
                    .orElseThrow(() -> new RuntimeException("user not found"));

            final TodoEntity todo = new TodoEntity();

            todo.setCreatedBy(creator);
            todo.setDetails(command.details());
            todo.setCompleted(false);

            final TodoEntity saved = todoRepository.save(todo);

            TodoEvent todoEvent = TodoEvent.newBuilder()
                    .setComplete(saved.getCompleted())
                    .setDetails(saved.getDetails())
                    .setId(saved.getId().toString())
                    .setEventType("CREATED")
                    .build();


            final byte[] bytes = serializer.serialize("outbox.event.TODO", todoEvent);

            eventPublisher.publish(bytes,
                    "TODO",
                    "NEW_TODO",
                    saved.getId().toString());


            return todoMapper.convert(todo);

        };

        return transactionHelper.executeTx(todoEntitySupplier);
    }
```


- The Kafka connector
```json
{
  "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
  "database.dbname": "todo",
  "database.hostname": "db",
  "database.password": "postgres",
  "database.user": "postgres",
  "key.converter.schema.registry.url": "http://redpanda:8081",
  "key.convertor": "org.apache.kafka.connect.storage.StringConverter",
  "name": "todo-outbox",
  "plugin.name": "pgoutput",
  "table.include.list": "public.outbox_entity",
  "topic.prefix": "todo",
  "transforms": "outbox",
  "transforms.outbox.type": "io.debezium.transforms.outbox.EventRouter",
  "value.converter": "io.debezium.converters.BinaryDataConverter",
  "value.converter.delegate.converter.type": "org.apache.kafka.connect.json.JsonConverter",
  "value.converter.delegate.converter.type.schemas.enable": "false",
  "value.converter.schema.registry.url": "http://redpanda:8081"
}
```


 This is where we combine our intent to save changes to an object, with our commitment to 



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
- Get rid of the outbox table & use Kafka connect directly on tables ? 
  - lose the schema guarantees






# Ok - so how does it work ?

Technically speaking - this is a log tailing producer




# Transactional Guarantee
  


  
  
# Schema Evolution Guarantee

- The [Kafka Avro serialization code that packs the schema id into the message](https://github.com/confluentinc/schema-registry/blob/75f323987274afc8844f47012bd83285e873414c/avro-serializer/src/main/java/io/confluent/kafka/serializers/AbstractKafkaAvroSerializer.java#L133)



# Credit to

In tech, we stand on the shoulder of giants. A heartfelt thanks to the work of the following individuals for thier brilliant work than enabled this article.

 - Chris Richardson
 - Gunnar Morling

