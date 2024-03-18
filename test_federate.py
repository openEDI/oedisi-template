import json
import logging
from datetime import datetime

import helics as h
from oedisi.types.common import BrokerConfig
from oedisi.types.data_types import VoltageArray
from pydantic import BaseModel

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


class TestFederateConfig(BaseModel):
    """Pydantic model for the static configuration of the federate."""

    name: str  # Name of federate
    input_needed_at_startup: float  # See component_definition.json


class TestFederate:
    def __init__(
        self,
        config: TestFederateConfig,
        input_mapping: dict[str, str],
        broker_config: BrokerConfig,
    ):
        """Template federate to get you started.

        Parameters
        ----------
        config : TestFederateConfig
            Static configuration including the federate name and input needed at startup.
        input_mapping : dict[str,str]
            Maps any dynamic inputs to helics subscription keys. In this example,
            there are none.
        broker_config : BrokerConfig
            Configures the helics broker ip and port. Default is 127.0.0.1:23404.
        """
        # Create HELICS Federate object that describes the federate properties
        fedinfo = h.helicsCreateFederateInfo()
        fedinfo.core_name = config.name  # Sets HELICS name
        fedinfo.core_type = (
            h.HELICS_CORE_TYPE_ZMQ
        )  # OEDISI simulations use ZMQ transport layer
        fedinfo.core_init = "--federates=1"
        h.helicsFederateInfoSetBroker(fedinfo, broker_config.broker_ip)
        h.helicsFederateInfoSetBrokerPort(fedinfo, broker_config.broker_port)

        # Maximum time resolution. Time unit may depend on simulation type.
        h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_delta, 0.01)

        self.vfed = h.helicsCreateValueFederate(config.name, fedinfo)
        logger.info("Value federate created")

        # Register any subscriptions you may have
        # self.sub_example = self.vfed.register_subscription(
        #    input_mapping["subscription_name"], ""
        # )

        # This should match the dynamic output in component_definition.json
        self.pub_example = self.vfed.register_publication(
            "appropriate_helics_pub", h.HELICS_DATA_TYPE_DOUBLE, ""
        )

    def run(self):
        """Run HELICS simulation until completion."""
        # Starts HELICS simulation. Essentially says to broker "This simulation is ready"
        self.vfed.enter_executing_mode()
        logger.info("Entering execution mode")

        # We request the time we want
        granted_time = h.helicsFederateRequestTime(self.vfed, 0.0)
        while granted_time < 100.0:
            logger.info("start time: " + str(datetime.now()))

            self.pub_measurement.publish(
                # If possible, use either basic types available like floats, ints, etc, or types provided
                # by the oedisi.types.data_types module.
                # Any indexing information should have appropriate labels if necessary.
                VoltageArray(values=[0.0, 1.0, 2.0], ids=["node1", "node2", "node3"])
            )

            granted_time = h.helicsFederateRequestTime(self.vfed, int(granted_time) + 1)
            logger.info("end time: " + str(datetime.now()))

        self.destroy()

    def destroy(self):
        "Clears memory and frees memory from HELICS>"
        h.helicsFederateDisconnect(self.vfed)
        logger.info("Federate disconnected")
        h.helicsFederateFree(self.vfed)
        h.helicsCloseLibrary()


def run_simulator(broker_config: BrokerConfig):
    """Creates and runs HELICS simulation."""

    # Static inputs are always defined in a static_inputs.json
    with open("static_inputs.json") as f:
        config = TestFederateConfig(**json.load(f))

    # Any HELICS subscriptions should use input_mapping.json
    with open("input_mapping.json") as f:
        input_mapping = json.load(f)

    sfed = TestFederate(config, input_mapping, broker_config)
    sfed.run()


if __name__ == "__main__":
    run_simulator(BrokerConfig(broker_ip="127.0.0.1"))
