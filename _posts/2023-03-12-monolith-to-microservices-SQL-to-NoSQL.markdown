---
layout: post
title:  "Monoliths to Microservices, SQL to NoSQL"
date:   2023-03-12 14:52:29 +1100
categories: MySQL, scyalladb, springboot
---
# Introduction

Sometimes, near enough **is** good enough. When decomposing monoliths & building services that are intended to scale, sometimes we can comprimise on refferential integrity to unlock other useful behaviours

In this article, I'll walk you a based-on-a-true story series of technical details & implmentation decisions, with some sample code, in the hope that I give the reader an insight into Monolith decomposition & a new way of thinking about refferential integrity.

## Introducing The Monolith

Let's have a look at an example monolithic application, from the database up

```sql

create table
  doctors (
    id bigint primary key not null AUTO_INCREMENT,
    email varchar(35) not null,
    name varchar(50) not null,
    active boolean default false,
    constraint email_uniq unique (email)
  );


create table
  patients (
    id bigint primary key not null AUTO_INCREMENT,
    email varchar(35) not null,
    name varchar(50) not null,
    constraint email_uniq unique (email)
  );


create table
  appointments (
    id bigint primary key not null AUTO_INCREMENT,
    patient_id bigint,
    doctor_id bigint not null,
    scheduled_start_time TIMESTAMP,
    scheduled_end_time TIMESTAMP,
    actual_start_time TIMESTAMP,
    actual_end_time TIMESTAMP,
    FOREIGN KEY (patient_id) references patients (id),
    FOREIGN KEY (doctor_id) references doctors (id) on delete cascade -- TODO refactor this to a trigger to delete unbooked 
  );
```

# What does this tell us about the application ?

- All appointments are created for doctor, whom we know exists
- When a doctor is deleted, so are thier appointments
- When an appointment is updated to be assigned to a patient, that patient must also exist!


# Let's decompose the Monolith !


# Let's talk to our product manager








