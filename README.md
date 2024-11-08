# L3

## How To Run For Developers: 

1. Create a Venv and install all the necessary dependencies listed in `requirements.txt`

2. Create a `.env` file at the root directory and populate with:
```
RIOT_API_KEY="L3 RIOT API key"
RIOT_BASE_URL=https://americas.api.riotgames.com
BUCKET_NAME="l3-bucket"
AWS_ACCESS_KEY_ID="aws group access key ID"
AWS_SECRET_ACCESS_KEY="aws group access key""
AWS_SESSION_TOKEN="aws session token"
```
> Once we move our code to EC2 we won't need  `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`. For now just hardcode them here for testing purposes (also these tokens expire, so need to update periodically).

3. Upload `L3_keypair.pem` to root directory. This allows connection to EC2 instance. **REMEMBER TO TURN OFF EC2 INSTANCE**

4. Run `python main.py` from root directory
