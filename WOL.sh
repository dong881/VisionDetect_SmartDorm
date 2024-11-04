#!/bin/bash
source "$(dirname "$0")/.env"
etherwake "$TARGET_MAC"
