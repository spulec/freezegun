"""
Lazy module aims to reproduce the context of late loaded modules
Eg. testing a django view using the test client
"""

def load():
    import time

    class TimeAsClassAttribute:
        """
        Reproduce the behaviour of: rest_framework.throttling.SimpleRateThrottle
        see: https://github.com/encode/django-rest-framework/blob/3.13.1/rest_framework/throttling.py#L63
        """
        _time = time.time

        def call_time(self):
            return self._time()

    globals()["TimeAsClassAttribute"] = TimeAsClassAttribute
