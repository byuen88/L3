# L3

## How To Run For Developers: 

1. Create a Venv and install all the necessary dependencies listed in `requirements.txt`

2. Create a `.env` file at the root directory and populate with:
```
RIOT_API_KEY=<L3 RIOT API key>
RIOT_BASE_URL=https://americas.api.riotgames.com
BUCKET_NAME="l3-bucket"
REGION_NAME="ca-central-1"
AWS_ACCESS_KEY_ID=<aws group access key ID>
AWS_SECRET_ACCESS_KEY=<aws group access key>
AWS_SESSION_TOKEN=<aws session token>
```
> Once we move our code to EC2 we won't need  `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`. For now just hardcode them here for testing purposes (also these tokens expire, so need to update periodically).

3. Upload `L3_keypair.pem` to root directory. This allows connection to EC2 instance. **REMEMBER TO TURN OFF EC2 INSTANCE**

4. Run `python main.py` from L3 root directory

## Containerize L3

### Running Image Locally
1. From the L3 root directory, run `docker build -t <image_name> -f DOCKER/Dockerfile .`
2. Run the image with `docker run -it <image_name>`

### Running Image on EC2
Cherry will try to always upload the latest L3 image to the EC2, so ideally, you can just SSH into the EC2 and run the image with `docker run -it -v /home/ec2-user/L3:/app/data l3`. Any persistent files like `combined.json` and `last_update_time` will be stored in `~/L3`. However, if you want to test your own changes on EC2, follow the steps below:
1. Make sure to get rid of `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN` in `.env`. Otherwise you might get an error saying `The provided token has expired.` when running the image on EC2.
2. In `L3\services\bucket_services.py`, do the #TODO (comment out and uncomment lines)
2. From the L3 root directory, run `docker build -t <image_name> -f DOCKER/Dockerfile .`
3. `docker save <image_name> | gzip > <image_name>.tar.gz`
4. `scp -i L3_keypair.pem l3.tar.gz ec2-user@<ip_addr>:~/L3`
5. SSH to EC2 instance and run `docker load < <image_name>`
6. `docker run -it -v /home/ec2-user/<volume_dir>:/app/data <image_name>`
7. Any persistent files will be stored in `/home/ec2-user/<volume_dir>`