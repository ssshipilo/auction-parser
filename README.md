### Installing Firefox

```
sudo apt update
sudo apt install firefox -y
```

### Install Geckodriver
```cmd
GECKODRIVER_VERSION=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest | grep 'tag_name' | cut -d\” -f4)
wget https://github.com/mozilla/geckodriver/releases/download/$GECKODRIVER_VERSION/geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz
tar -xvzf geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz
```

```cmd
sudo mv geckodriver /usr/local/bin/
```

### Running the script: 
python3 get.py