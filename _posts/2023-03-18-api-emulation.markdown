---
layout: post
title:  "API emulation, compatibility & re-implementation - testing tools, compatibility layers, or a business model"
date:   2023-03-18 
categories:  api, emulation, golang, Redpanda, Pulsar, 
---

## Abstract

Strong API Boundaries are fundamental to building & evolving software with confidence & stability. 
As a Software Engineer, having the skill to emulate an existing API unlocks some powerful testing & development techniques. Being able to analyse API compatible products is key to being able to make technical decisions on choosing cloud & SaaS providers

In this article, I'll share a few examples from my experience 

### On composition 

Software systems are frequently composed of other smaller systems.

This idea of composition goes at least as far back as the UNIX pipe

<iframe width="420" height="315" src="https://www.youtube.com/embed/bKzonnwoR2I" frameborder="0" ></iframe>

Composition is the cornerstone of building modern backend services. When the business need arises for engieers build a backend system that

- stores information
- caches data for fast retrival
- publishes events about state changes within the application

It is exceedingly rare that any of the components are written from scratch, nor that they are deeply entangled with each other. Instead, this new service might be composed of

- A backend web framework to build an API
- A database to delegate storage to
- A purpose built distributed cache for optimal performance
- An Event publishing mechanism used to signal changes to the ecosystem outside the service

and that 

- the integration of the database & the api depends on a database protocol - Postgres, MySQL, DynamoDB etc 
- the redis integration depends on the Redis protocol
- the event publishing mechanism depends on a messaging protocol - kafka - rabbitmq, jms etc. 

I'm sure the details of this are not necessarily new - What I'm hoping to convey is that whether you knew it or not :
- you were already using composition to build backend services
- your comfort with composition extends as far as you have api compatibility - if you chose a particular set of apis, you do so knowing those APIs scale well enough for the foreseeable future, 

<br />




### Use cases

In  this section, I'll cover some of my experience as a Software Engineer for where I've seen API Emulation used, & the mechanism by which they are emulated

<br />

#### GCP Emulators

GCP provide a suite of emulators for thier stack, that give engineers the ability to run basic tests against an ephemeral container that implements the API - great for local development or CI/CD pipelines to give some basic confidence that your service continues to meet basic api & behaviour guidelines.

<br />


##### How?
Google's gRPC framework is used across a lot of these products. gRPC services are defined in protobuf idls
Generating a server definition is trivial in the supported languages 
TODO generated server stubs


TDOD link to gist from zoomymq 

#### Load & Integration Testing

In a previous role, we composed a system from custom REST APIs we write, some serverless databases & message queues, and a  SaaS product that sent SMS. 

![Diagram](/assets/sms_emulator/sms_emulator.png)
<br />


The SMS SaaS was critical to the infrastructure, but was quite expensive on a per-request basis, & had real world side effects that where not compatible with rapid experimentation. 

We wanted to run load/capacity/tests  against our rest apis & the cloud services we were using to prove that our autoscaling rules worked & to validate our architecture, without incurring the costs of using the SaaS product.

Unfortunately, the SaaS product did not provide a test environment, nor an open source tier. However, they did provide a strong API contract, meaning we had to write an emulator
<br />

![Diagram](/assets/sms_emulator/sms_emulator_load_test/sms_emulator_load_test.png)
<br />


##### How did we do it?

This one is actually relatively straightforward. Because the SaaS was REST based and published a Swagger specification, we generated a new Spring project, added Swagger definitions, and had a project skeleton in minutes. Within a few days, we had functional emulator!

Here's an example Using [Telstra's SMS Api](https://dev.telstra.com/content/messaging-api), Maven & spring boot

![Diagram](/assets/openapicodegen.png)

The Swagger spec
```yaml
  /messages/sms:
    post:
      description: |
        Send an SMS Message to a single or multiple mobile number/s.
      summary: Send SMS
      tags:
        - Messaging
      operationId: sendSms
      consumes:
        - application/json
      produces:
        - application/json
      parameters:
        - name: payload
          in: body
          required: true
          description: |
            A JSON or XML payload containing the recipient's phone number and text message.
            This number can be in international format if preceded by a '+' or in national format ('04xxxxxxxx') where x is a digit.
          schema:
            $ref: '#/definitions/SendSMSRequest'
      responses:
        '201':
          description: Created
```

The Generated interface
```java
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2023-03-18T12:32:45.609184+11:00[Australia/Melbourne]")
@Validated
@Api(value = "messages", description = "the messages API")
public interface MessagesApi {
    ...
     @ApiOperation(value = "Send SMS", nickname = "sendSms", notes = "Send an SMS Message to a single or multiple mobile number/s. ", response = MessageSentResponseSms.class, authorizations = {
        @Authorization(value = "auth", scopes = {
            @AuthorizationScope(scope = "NSMS", description = "NSMS") })
         }, tags={ "Messaging", })
    @ApiResponses(value = { 
        @ApiResponse(code = 201, message = "Created", response = MessageSentResponseSms.class),
        @ApiResponse(code = 400, message = "You may receive any of the below error message if API is unable to send SMS. While we work on improving the error handling through service error codes, check for the corrective action against each error message. Please reach out to telstradev@team.telstra.com if error persists. Invalid 'from' address specified - Ensure the 'from' field is as per API reference doc.  DELIVERY-IMPOSSIBLE - Check the 'to' field and ensure it is a valid phone number as per API reference doc.  FROM-MSISDN-TOO-LONG - Ensure the from address is not more than 15 chars in length.  BODY-TOO-LONG - Request BODY cannot be more than 1999 UTF-8 characters for single recipient and 1998 UTF-8 characters for multiple recipients.  BODY-MISSING. Request BODY is missing. Ensure appropriate request BODY is included as per the API reference doc.  TO-MSISDN-TOO-LONG - Ensure phone number is in E.164 format. This number can be in international format \"to\": \"+61412345678\" or in national format \"0412345678\". Can be an array of strings if sending to multiple numbers: \"to\":[\"+61412345678\", \"+61418765432\"].  TO-MSISDN-NOT-VALID - Ensure 'to' field's value is a valid phone number in E.164 format.  TECH-ERR - Send the details to telstradev@team.telstra.com for troubleshooting this issue.  BODY-NOT-VALID - Ensure Body does not contain characters other than UTF-8.  NOT-PROVISIONED - Check get subscription is returning successful response, if not, run create subscription and try again. If issue persists e-mail telstradev@team.telstra.com.  Request flagged as containing suspicious content. Please check the request content but if problem persists contact support at telstradev@team.telstra.com with details of the request.  FREE-TRIAL-NO-BNUM - For Free Trial App only. Run free trial bnum register before sending SMS.  FREE-TRIAL-INVALID-BNUM - Free Trial apps are only allowed to send to specified destination numbers. Verify that all your destination numbers are in your list.  TO-MSISDN-OVER-ALLOWED-LIMIT-OF-NUMBERS or TOO MANY DESTINATIONS - Do not use more than 10 recipients in a single call and ensure replyRequest=false or remove the [ ] brackets when using single recipient.  Refer to the sample code for Send SMS in the link for more details: https://dev.telstra.com/content/messaging-api#operation/sendSms "),
        @ApiResponse(code = 401, message = "Invalid access token. Please try with a valid token: Either the token has expired or incorrect token was used. <br/><br/> OR <br/><br/> Invalid API call as no apiproduct match found: If you are using credit card as billing method, Messaging API product has not been added to your Apps & Keys. Please re-run 'post' Authentication and use the updated token. Refer to the sample code for generate authentication token in the link for more details https://dev.telstra.com/content/messaging-api#section/Authentication  If problem persists, write a post in the Messaging API forum https://dev.telstra.com/forums/messaging-api-forum for the TelstraDev admin to check the issue. "),
        @ApiResponse(code = 403, message = "Authorization credentials passed and accepted but account does not have permission. <br/><br/> OR <br/><br/> MSG_Monetization_ERR. Credit Card API limit may have been reached, e-mail telstradev@team.telstra.com for support. If you are using the Free Trial account, this error shows you have exceeded the number of free messages available. <br/><br/> OR <br/><br/> SpikeArrest. The API call rate limit has been exceeded You will receive a SpikeArrest error in two possible situations:              A: You have exceeded your free trial quota. If you would like to continue using the Messaging API, please upgrade to a paid plan by creating a company with Telstra Billing details (not, credit card is no longer accepted for this API product).  B: Concurrent API Calls are higher than supported, reduce the concurrent calls and try again. If problem persists, contact us at telstradev@team.telstra.com "),
        @ApiResponse(code = 404, message = "RESOURCE-NOT-FOUND - Subscription Expired. Re-provision your MSISDN through create subscription call using the same client credentials and try sending an SMS again. <br/><br/> OR <br/><br/> TO-MSISDN-NOT-VALID. Invalid resource: verify that a valid destination number is used. <br/><br/> OR <br/><br/> RESOURCE-NOT-FOUND. The requested URI does not exist. Ensure a correct URL is used. The correct URL can be found in the sample code section of: https://dev.telstra.com/content/messaging-api#operation/createSubscription "),
        @ApiResponse(code = 405, message = "Only POST and GET methods are supported.  Read the documentation for send SMS : https://dev.telstra.com/content/messaging-api#operation/sendSms "),
        @ApiResponse(code = 415, message = "API does not support the requested content type"),
        @ApiResponse(code = 422, message = "The request is formed correctly, but due to some condition the request cannot be processed e.g. email is required and it is not provided in the request "),
        @ApiResponse(code = 429, message = "Too Many Requests.  Concurrent API Calls are higher than supported, reduce the concurrent calls and try again. If problem persists, contact us at telstradev@team.telstra.com "),
        @ApiResponse(code = 500, message = "Technical error : A server error has occurred while processing your request or the endpoints provided does not exist in the API.  Please correct the API endpoint and try again. If the error persists even after re-try, check our https://dev.telstra.com/api/status page to ensure the service is up and running. If the service is not up and running check our forum page https://dev.telstra.com/forums/api-live-status-page and leave a post to confirm the outage for the Telstradev admin to check the issue. "),
        @ApiResponse(code = 501, message = "The HTTP method being used has not yet been implemented for the requested resource "),
        @ApiResponse(code = 503, message = "The service requested is currently unavailable.  Please correct the API endpoint and try again. If the error persists even after re-try, check our https://dev.telstra.com/api/status page to ensure the service is up and running. If the service is not up and running check our forum page https://dev.telstra.com/forums/api-live-status-page and leave a post to confirm the outage for the Telstradev admin to check the issue. "),
        @ApiResponse(code = 200, message = "An internal error occurred when processing the request.  Please correct the API endpoint and try again. If the error persists even after re-try, check our https://dev.telstra.com/api/status page to ensure the service is up and running. If the service is not up and running check our forum page https://dev.telstra.com/forums/api-live-status-page and leave a post to confirm the outage for the Telstradev admin to check the issue. ") })
    @PostMapping(
        value = "/messages/sms",
        produces = { "application/json" },
        consumes = { "application/json" }
    )
    default ResponseEntity<MessageSentResponseSms> sendSms(@ApiParam(value = "A JSON or XML payload containing the recipient's phone number and text message. This number can be in international format if preceded by a '+' or in national format ('04xxxxxxxx') where x is a digit. " ,required=true )  @Valid @RequestBody SendSMSRequest payload) {
        getRequest().ifPresent(request -> {
            for (MediaType mediaType: MediaType.parseMediaTypes(request.getHeader("Accept"))) {
                if (mediaType.isCompatibleWith(MediaType.valueOf("application/json"))) {
                    String exampleString = "{ \"country\" : [ { \"AUS\" : 1 } ], \"numberSegments\" : 1, \"messageType\" : \"SMS\", \"messages\" : [ { \"messageStatusURL\" : \"https://tapi.telstra.com/v2/messages/sms/d997474900097a1f0000000008d7e18102cc0901-1261412345678/status\n\", \"messageId\" : \"d997474900097a1f0000000008d7e18102cc0901-1261412345678\", \"to\" : \"+61412345678\", \"deliveryStatus\" : \"MessageWaiting\" }, { \"messageStatusURL\" : \"https://tapi.telstra.com/v2/messages/sms/d997474900097a1f0000000008d7e18102cc0901-1261412345678/status\n\", \"messageId\" : \"d997474900097a1f0000000008d7e18102cc0901-1261412345678\", \"to\" : \"+61412345678\", \"deliveryStatus\" : \"MessageWaiting\" } ] }";
                    ApiUtil.setExampleResponse(request, "application/json", exampleString);
                    break;
                }
            }
        });
        return new ResponseEntity<>(HttpStatus.NOT_IMPLEMENTED);

    }

    ...
}
```

The Emulator Implementation
```java 

@RestController
public class MessagesApiImpl implements MessagesApi {
    ...
    @Override
    public ResponseEntity<MessageSentResponseMms> sendMms(SendMmsRequest body) {
        return messageEmulatorService.handleSend(body);
    }
    ...
}

```

The client applications when deployed to the load test environment simply used a different url 
```java
    @Bean
    public com.telstra.ApiClient smsClient() {
        com.telstra.ApiClient client = Configuration.getDefaultApiClient();
        client.setBasePath("https://fake-emulator-host.com"); 
        return client;
    }
```



#### For profit! 

##### Redpanda 
Redpanda are a company that built and support the Redpanda message broker, a c++ Apache Kafka compatible message broker. 
The business proposal of Redpanda is pretty simple - cheap/fast/stable Kafka. With no JVM, no garbage collection !  

###### How ?

Not quite as easy as the gRPC & OpenAPi mechnaisms! 

Redpanda re implmemented the [kafka binray protocol](https://kafka.apache.org/protocol#:~:text=Kafka%20uses%20a%20binary%20protocol,of%20the%20following%20primitive%20types.)




##### The near infinite Postgresql compatibile-ish databases



- [Redshift](https://docs.aws.amazon.com/redshift/latest/dg/c_redshift-and-postgres-sql.html) for analytics
- [CockroachDB](https://www.cockroachlabs.com/product/) for highly available global systems 
- [AlloyDB](https://cloud.google.com/alloydb) for some comprimise between the two

###### How ?

Could be [Foreign Data Warppers](https://wiki.postgresql.org/wiki/Foreign_data_wrappers)



#### Microservice decomposition , Strangler Fig




#### Opaque Deprecation

This is the least interesting but possibly the most liberating of all the examples I've seen. This focuses on the idea of data liberation. 

Imagine a crusty old SOAP API that had consumers that are not ready to move away from. Data is Authored in that system via th SOAP API is used throughout A monolithic application


Step one





### Sumamry








