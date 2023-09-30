import zmq
from spacemouse_server import ZMQ_CFG
import numpy as np
import cereal.messaging as messaging

from openpilot.common.realtime import Ratekeeper

pm, sm = None, None


if __name__ == "__main__":
    pm = messaging.PubMaster(["testJoystick"])

    rk = Ratekeeper(20.0)

    ip = ZMQ_CFG["PC"]["IP"]
    sub_port = ZMQ_CFG["PC"]["PUB_PORT"]

    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)

    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
    subscriber.connect(f"tcp://{ip}:{sub_port}")

    recv_kwargs = {"flags": zmq.NOBLOCK}

    try:
        while True:
            message = subscriber.recv()

            if message is None:
                continue
            action = np.frombuffer(message)
            msg = messaging.new_message("testJoystick")
            msg.testJoystick.axes = [float(action[0]), float(action[1])]
            msg.testJoystick.buttons = [False]

            # TODO: change this to standard robot api, pretty kludgy way of doing things currentl0y
            pm.send("testJoystick", msg)

            # TODO: precise loop timing here
            rk.keep_time()

    except KeyboardInterrupt:
        print("stopping client controller!")
