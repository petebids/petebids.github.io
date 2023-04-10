---
layout: post
title:  "What does an enterprise grade Spring boot application look like in 2023"
date:   2023-04-2 
categories:  Spring Boot , SaaS
---

## Abstract


A frequent ask from younger developers & college students on [r/SpringBoot](https://www.reddit.com/r/SpringBoot/) goes along the lines of
"I've done xyz tutorials, what does a  *real* Spring Boot application look like ? "

Having built enterprise applications in SpringBoot since 2018, I'll share some insights to hopefully fill in some blanks. 
In this article, I'll make a lot of generalisations for the purpose of giving a single coherent idea,
and refer to an example I've implemented on [GitHub](https://github.com/petebids/todo-tx-outbox). 




## Security

Generally speaking, new applications are built in a microservices style, & implement the [Resource server](https://www.rfc-editor.org/rfc/rfc6749#section-1.1) pattern.
What this means is that a central team builds and or runs some SaaS that plays the role of the authorization server. 
When you start building a new service, you add the resource server dependency (or some internal library that performs the same purpose) & apply some minimal configuration





## Package structure & Code style

Generally speaking, Enterprise code tries to be as a structured  & formulaic as possible, for the purpose of [low cognitive load](https://en.wikipedia.org/wiki/Cognitive_load)
There are good reasons for this, as it means reshuffling service ownership amongst teams or helping another team out in a crisis becomes easier, if everyone's code looks the same
If you are working on something new & feeling overwhelmed, it's much easier knowing which package classes belong in, or how to structure a new feature

# Lombok

Although [Java Records](https://docs.oracle.com/en/java/javase/14/language/records.html) and other advances in the Java ecosystem are great,



# Mapstruct



# Package structure - what goes where? 




## 12 Factor apps

The 12 factor principles are a standard for building backend applications for the modern web. It's important to [read and understand](https://12factor.net/) 
why in the abstract before trying ti implement these practices in your spring application.


# We don't use the @Scheduled annotation

Whilst the scheduled annotation is a powerful tool with low overhead, it adds some state into your application that is antithetical with a 12 factor app. 
If you deploy in a horizontally scaled manner, there may be  2, 10, or 200 instances of your application at any given time, 
and those instances can & will bve shutdown at any time. 
If you only want a @Scheduled job to run once, you need to implement leader election,
& deal with the potential of race conditions of scheduled jobs & container shutdown,. 

Instead, the invocation of a scheduled process is extracted from the application,  & delegated 


# Docker Compose for local development 

To fulfil the [dev/prod parity](https://12factor.net/dev-prod-parity) principle, [Docker Compose](https://docs.docker.com/compose/) is frequently used.
By being able to 

## 