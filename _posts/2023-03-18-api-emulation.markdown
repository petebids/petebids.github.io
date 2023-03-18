---
layout: post
title:  "API emulation, compatibility & re-implmentation - testing tools, compatibility layers, or a business model"
date:   2023-03-18 
categories:  api, emulation, golang, Redpanda, Pulsar, 
---

## Abstract

Strong API Boundaries are fundamental to building & evolving software with confidence & stability. 
As an Software Engineer, having the skill to emulate an existing API unlocks some poswerful testing & development techniques. 

In this article, we will look at a few examples of how API emulation

### On composability 

Software systems are frequently composed of other smaller systems or progrmaming. 

This idea of composability goes at least as far back as the UNIX pipe

<iframe width="420" height="315" src="https://www.youtube.com/watch?v=bKzonnwoR2I" frameborder="0" ></iframe>

Composability is the cornerstone of building modern backend services. When the business need arises for engieers build a backend system that

- stores information
- sends email notifications
- caches data for fast retrival
- publishes events about state changes within the application

It is exceedingly rare that any of the componenets are written from scratch, nor that they are deeply entangled with each other. Instead, this new service might be composed of

- A backend web framework to build an API
- A database to delegate storage to
- A purpose built  cache like Redis
- An Event Streaming platform like Kafka

and that 

- the integration of the database & the api uses the JDBC API & the database dialect (e.g. Postgresql)
- the redis integration depends on the Redis protocl
- the event publishing mechanism 

I'm sure the deatils of this are not necessarily new - What i'm hoping to convey is that whether you knew it or not, you were already using composability! 



### Use cases

In  this section, I'll cover some of my experince as a Software Engineer for where I've seen API Emulation used, & the mechanism by which they are emulated

#### GCP Emulators

GCP provide a suite of emulators for thier stack, that give engineers the ability to run basic tests against an ephemeral container that implmenets the API - great for local development or CI/CD pipelines to give some basic confidence that your service continues to meet basic api & behaviour guidelines.

##### How?
Google's gRPC framework is used across a lot of these products. gRPC services are defined in protobuf idls
Generating a server definition is trivial in the supported languages 
TODO generated server stubs


TDOD link to gist from zoomymq 

#### Load & Integration Testing

In a previous role, we composed a system from custom REST APIs we write, some serverless databases & message queues, and a  SaaS product that sent SMS. 

The SMS SaaS was critical to the infrastucture, but was quite expensive on a per request basis, & had real workd side effects that where not compatible with rapid experimentation. 

We wanted to run load/capacity/tests  against our rest apis & the cloud services we were using to prove thst our autoscaling rules worked & to validate our architecture, without incurring the costs of using the SaaS product.

Unfortunatley, the SaaS product did not provide a test environment, not an open source tier. However, they did provide a strong API contract, meaning ..

##### How?

TODO Gist for OpemAPI Codegen

Timecost - minutes to get a controller - 


#### For profit! 

##### Redpanda 
Redpanda area company that built and support the Redpanda message broker, a c++ Apache Kafka compatible message broker. 
The business proposal of Redpanda is pretty simple - cheap/fast Kafka. 

###### How ?

Not quite as easy as the gRPC & OpenAPi mechnaisms! 

Redpanda re implmemented the [kafka binray protocol](https://kafka.apache.org/protocol#:~:text=Kafka%20uses%20a%20binary%20protocol,of%20the%20following%20primitive%20types.)




##### The near infinite Postgresql compatibile-ish databases



- [Redshift](https://docs.aws.amazon.com/redshift/latest/dg/c_redshift-and-postgres-sql.html) for analytics
- [CockroachDB](https://www.cockroachlabs.com/product/) for high availability, global systems 
- [AlloyDB](https://cloud.google.com/alloydb) for some comprimise between the two

###### How ?

Could be [Foreign Data Warppers](https://wiki.postgresql.org/wiki/Foreign_data_wrappers)



#### Microservice decomposition , Strangler Fig






