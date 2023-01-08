#!/usr/bin/env python3

import argparse
from itertools import cycle
import logging
import os
import socket
import time
from typing import List

from PIL import Image, ImageSequence

from matrix_pdu import FramePDU, CommandPDU


LEDSERVER_HOST = os.environ.get("LEDSERVER_HOST", "10.20.0.26")
LEDSERVER_PORT = int(os.environ.get("LEDSERVER_PORT", "20304"))
DESTINATION_PANEL = (LEDSERVER_HOST, LEDSERVER_PORT)

LED_WIDTH = int(os.environ.get("LED_WIDTH", "32"))
LED_HEIGHT = int(os.environ.get("LED_HEIGHT", "16"))
PANEL_SIZE = (LED_WIDTH, LED_HEIGHT)


logging.basicConfig(
    format="%(asctime)s [%(levelname)-8s] %(message)s",
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)


class GifFrame:
    frame: FramePDU
    delay_ms: int

    def __init__(self, frame, delay_ms) -> None:
        self.frame = frame
        self.delay_ms = delay_ms


def send_pdu(frame: FramePDU, destination: tuple):
    pdu_bytes = frame.as_binary()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(destination)
    s.sendall(pdu_bytes)
    s.close()


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str)
    parser.add_argument("--brightness", type=int, default=20)
    parser.add_argument("--priority", type=int, default=6)
    args = parser.parse_args()

    logging.info(f"Sending {args.file} to tcp://{LEDSERVER_HOST}:{LEDSERVER_PORT}/")

    logging.info(f"Setting brightness to {args.brightness}")
    send_pdu(CommandPDU(CommandPDU.CMD_BRIGHTNESS, args.brightness), DESTINATION_PANEL)

    logging.info(f"Setting priority to {args.priority}")
    send_pdu(CommandPDU(CommandPDU.CMD_PRIORITY, args.priority), DESTINATION_PANEL)

    total_duration = 0

    gif_frames: List[GifFrame] = []
    with Image.open(args.file) as gif:
        for im in ImageSequence.Iterator(gif):
            frame = FramePDU.from_image(im.resize(size=PANEL_SIZE, resample=Image.BILINEAR))
            duration = int(im.info.get("duration", 0))
            if duration < 40:
                duration = 0
            total_duration += duration
            gif_frames.append(GifFrame(frame=frame, delay_ms=duration))

    logging.info(f"Finished decoding GIF. Total duration = {total_duration/1000:.2f}s.")
    logging.info("Looping GIF to panel")

    for frame in cycle(gif_frames):
        try:
            send_pdu(frame.frame, DESTINATION_PANEL)
        except OSError as e:
            logging.exception("Error while sending packet", e)          
        time.sleep(frame.delay_ms/1000)


if __name__ == "__main__":
    main()
