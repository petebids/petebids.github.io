from diagrams import Cluster, Diagram
from diagrams.onprem.database import Postgresql
from diagrams.onprem.queue import Kafka
from diagrams.programming.framework import Spring
from diagrams.onprem.compute import Server

with Diagram("Transactional Outbox", show=False) as d:
    with Cluster("Microservice"):
        s = Spring()
        db = Postgresql()

    kc = Server("Kafka Connect")

    with Cluster("Kafka"):

        k = Kafka()

    s >> db << kc >> k 


