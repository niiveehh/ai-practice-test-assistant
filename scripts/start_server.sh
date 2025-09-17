#!/bin/bash
set -e

sudo chown -R ec2-user:ec2-user /home/ec2-user/PT_AI_Answer_Lambda
chmod -R 755 /home/ec2-user/PT_AI_Answer_Lambda

pkill -f streamlit || true

nohup /home/ec2-user/.local/bin/streamlit run /home/ec2-user/PT_AI_Answer_Lambda/app.py \
  --server.port 8501 --server.address 0.0.0.0 > /home/ec2-user/PT_AI_Answer_Lambda/streamlit.log 2>&1 &

