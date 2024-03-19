# Skynet
test project


First get Miniconda installed....

mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm -rf ~/miniconda3/miniconda.sh

Git clone this repo: git clone https://github.com/iideadeyeii/Skynet.git
cd Skynet
conda env create -f skynet.yml
conda activate skynet

You will need to modify the main.py file to include your API keys, as well as define where to pull the Logo Picture, i.e. /home/user/Skynet

When setup, execute with python main.py
