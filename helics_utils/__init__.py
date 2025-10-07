# -*- coding: utf-8 -*-
import helics as h


class Federate(object):
    def __init__(
        self,
        federate_name,
        subscriptions={},
        publications={},
        federate_initialize_string="--federates=1",
        delta_time=1,
    ):
        self.federate_name = federate_name
        fedinfo = h.helicsCreateFederateInfo()
        h.helicsFederateInfoSetCoreName(fedinfo, federate_name)
        h.helicsFederateInfoSetCoreTypeFromString(fedinfo, "zmq")
        h.helicsFederateInfoSetCoreInitString(fedinfo, federate_initialize_string)
        h.helicsFederateInfoSetIntegerProperty(fedinfo, h.helics_property_int_log_level, 7)
        h.helicsFederateInfoSetTimeProperty(
            fedinfo, h.helics_property_time_delta, delta_time
        )
        self.federate = h.helicsCreateValueFederate(federate_name, fedinfo)
        self.subscriptions = subscriptions
        self.publications = publications
        self.current_time = -1

    def register_subscription(self, topic):
        self.subscriptions[topic] = h.helicsFederateRegisterSubscription(
            self.federate, topic, ""
        )

    def register_publication(self, topic, kind):
        try:
            kind = getattr(h, f"helics_data_type_{kind}")
        except AttributeError:
            data_types = []
            for attr in h.__dict__:
                attr = str(attr)
                if "helics_data_type" in attr:
                    data_types.append(attr.replace("helics_data_type_", ""))
            print(f"{kind} must be in {data_types}")

        self.publications[topic] = h.helicsFederateRegisterGlobalPublication(
            self.federate, topic, kind, ""
        )

    def start(self):
        #h.helicsFederateInitialize(self.federate)
        h.helicsFederateEnterExecutingMode(self.federate)

    def advance(self, t):
        while self.current_time <= t:
            self.current_time = h.helicsFederateRequestTime(self.federate, t)

    def send(self, topic, value, kind):
        # TODO: support other types
        # TODO: publication should be based on registration
        if kind == "vector":
            h.helicsPublicationPublishVector(self.publications[topic], value)
        else:
            h.helicsPublicationPublishDouble(self.publications[topic], value)

    def recv(self, topic):
        return h.helicsInputGetString(self.subscriptions[topic])

    def __del__(self):
        h.helicsFederateDisconnect(self.federate)
        h.helicsFederateFree(self.federate)
        h.helicsCloseLibrary()


def setup_helics_federate(federate_name, subscriptions, publications):

    federate = Federate(federate_name)

    for s in subscriptions:
        federate.register_subscription(s)

    for p, k in publications:
        federate.register_publication(p, k)

    federate.start()

    return federate
