:
# Install Chrome
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - 
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
apt-get update 
apt-get install --no-install-recommends --assume-yes google-chrome-stable

# Install Chromedriver
wget -O /usr/local/share/chromedriver.zip "https://chromedriver.storage.googleapis.com/`curl https://chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip"
cd /usr/local/share
gunzip -f chromedriver.zip -S .zip
chmod 755 chromedriver
mv chromedriver /usr/local/bin
cd -
