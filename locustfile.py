from locust import HttpUser, task
from faker import Faker
from faker.providers import DynamicProvider
from datetime import datetime, timezone
from uuid import uuid4

level_provider = DynamicProvider(
    provider_name="level",
    elements=["error", "warn", "info", "debug"],
)

fake = Faker()

# then add new provider to faker instance
fake.add_provider(level_provider)


class HelloWorldUser(HttpUser):
    @task
    def hello_world(self):
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        print(timestamp)
        body = {
            "level": fake.level(),
            "message": fake.name(),
            "resourceId": str(uuid4()),
            "timestamp": timestamp,
            "traceId": str(uuid4()),
            "spanId": str(uuid4()),
            "commit": str(uuid4()),
            "metadata": {"parentResourceId": str(uuid4())},
        }
        self.client.post("/logs", json=body)
