#!/bin/bash
sudo yum install -y python3 python3-pip
python3 -m pip install --user --upgrade pip
python3 -m pip install --user -r /home/ec2-user/PT_AI_Answer_Lambda/requirements.txt

