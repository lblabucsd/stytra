from stytra.tracking.eyes import EyeTrackingMethod
from stytra.tracking.tail import CentroidTrackingMethod
from itertools import chain
from lightparam import Parametrized


class TailEyesTrackingMethod:
    name = "eyes_tail"
    processed_image_names = ["thresholded"]

    def __init__(self):
        super().__init__()
        self.method_chain = [CentroidTrackingMethod(), EyeTrackingMethod()]

        params = dict()
        for m in self.method_chain:
            params.update(m.detect.__annotations__)
        self.params = Parametrized(name="tracking/eyes_tail",
                                   params=params)

        headers = ["tail_sum"] + [
            "theta_{:02}".format(i) for i in range(self.params.n_segments)
        ]
        [
            headers.extend(
                [
                    "pos_x_e{}".format(i),
                    "pos_y_e{}".format(i),
                    "dim_x_e{}".format(i),
                    "dim_y_e{}".format(i),
                    "th_e{}".format(i),
                ]
            )
            for i in range(2)
        ]
        self.monitored_headers = ["tail_sum", "th_e0", "th_e1"]
        self.accumulator_headers = headers
        self.data_log_name = "behavior_tail_eyes_log"
        self.diagnostic_image = None


    def detect(self, im, **kwargs):
        messages = ""
        results = tuple()
        for met in self.method_chain:
            m, result = met.detect(im, **kwargs)
            messages += m
            results += tuple(result)

        if kwargs["display_processed"] == "thresholded":
            self.diagnostic_image = self.method_chain[1].diagnostic_image

        return messages, results

    def reset_state(self):
        headers = ["tail_sum"] + [
            "theta_{:02}".format(i) for i in range(self.params.n_segments)
        ]
        [
            headers.extend(
                [
                    "pos_x_e{}".format(i),
                    "pos_y_e{}".format(i),
                    "dim_x_e{}".format(i),
                    "dim_y_e{}".format(i),
                    "th_e{}".format(i),
                ]
            )
            for i in range(2)
        ]

        self.monitored_headers = ["tail_sum", "th_e0", "th_e1"]
        self.accumulator_headers = headers
