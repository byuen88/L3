# L3

## Run Application For Developers Locally

1. Create a Venv and install all the necessary dependencies listed in `requirements.txt`

2. Create a `.env` file at the root directory and populate with:
```
RIOT_API_KEY=<L3 RIOT API key>
RIOT_BASE_URL=https://americas.api.riotgames.com
BUCKET_NAME="l3-bucket"
REGION_NAME="ca-central-1"
```
3. To run the **CLI** application, run from the L3 root directory
```
python main.py
```
4. OR to run the **Web UI** application, run from the L3 root directory
```
python app.py
```

## Containerize L3

### Running Image Locally
1. From the L3 root directory, run `docker build -t <image_name> -f DOCKER/Dockerfile .`
2. Run the image with `docker run -it <image_name>`

### Running Image on EC2
SSH into the EC2 instance and run the application with 
```
docker run -d -p 5000:5000 -v /home/ec2-user/L3:/app/data l3
```
From a browser, access the application UI with the Public IPv4 address of the EC2 instance and port 5000. e.g. 3.98.58.160:5000
```
<Public IPv4 address>:5000
```
Any persistent files like `combined.json` and `last_update_time` will be stored in `~/L3`.

Stop the application with:
```
docker ps                       # to find the container_id
docker stop <container_id>
```

### Running Custom Image on EC2
If you want to test your own changes on EC2, follow the steps below:
1. From the L3 root directory, run `./deploy.sh <image_name> <ec2_ip_addr>`  **DO NOT GIVE image_name "L3"**
2. SSH to EC2 instance and run `docker run -d -p 5000:5000 -v /home/ec2-user/<volume_dir>:/app/data <image_name>`
5. Any persistent files will be stored in `/home/ec2-user/<volume_dir>`


