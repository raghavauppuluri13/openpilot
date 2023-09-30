import zmq

import numpy as np

import pickle

from spacemouse_driver import SpaceMouse
from openpilot.common.realtime import Ratekeeper

ZMQ_CFG = {
    "PC": {
        "IP": "192.168.63.109",
        "PUB_PORT": 5555,
    },
    "COMMA": {"IP": "192.168.63.80", "SUB_PORT": 5555},
}


def input2action(device):
    state = device.get_controller_state()
    # Note: Devices output rotation with x and z flipped to account for robots starting with gripper facing down
    #       Also note that the outputted rotation is an absolute rotation, while outputted dpos is delta pos
    #       Raw delta rotations from neutral user input is captured in raw_drotation (roll, pitch, yaw)
    dpos, rotation, raw_drotation, grasp, reset = (
        state["dpos"],
        state["rotation"],
        state["raw_drotation"],
        state["grasp"],
        state["reset"],
    )

    drotation = raw_drotation[[1, 0, 2]]

    action = None

    if not reset:
        drotation[2] = -drotation[2]
        drotation *= 300
        dpos *= 400
        drotation = drotation

        grasp = 1 if grasp else 0
        action = np.array(
            [-dpos[0], drotation[2], -drotation[1], grasp]
        )  # v_x, w_z, arm_cmd, grasp_suction

        action = np.clip(action, -1, 1)

        print(action)

    return action


if __name__ == "__main__":
    space_mouse = SpaceMouse()
    space_mouse.start_control()
    pub_port = ZMQ_CFG["PC"]["PUB_PORT"]

    context = zmq.Context()
    publisher = context.socket(zmq.PUB)

    # publisher
    publisher.bind(f"tcp://*:{pub_port}")

    rk = Ratekeeper(20.0)

    try:
        while True:
            action = input2action(space_mouse)
            publisher.send(action.tobytes())
            rk.keep_time()
    except KeyboardInterrupt:
        print("stopping spacemouse!")
