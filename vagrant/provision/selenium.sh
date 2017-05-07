:
# Install Java 8
# Add the Java PPA to our repo
add-apt-repository ppa:webupd8team/java
apt-get update && apt-get upgrade

# Sets things up so that we can accept the oracle liscence automatically
echo debconf shared/accepted-oracle-license-v1-1 select true | debconf-set-selections
echo debconf shared/accepted-oracle-license-v1-1 seen true | debconf-set-selections

# Install
apt-get install --no-install-recommends --assume-yes software-properties-common oracle-java8-installer

# Use Java 8 by default
update-java-alternatives -s java-8-oracle

# Install latest Selenium
wget -O /usr/local/share/selenium-server-standalone.jar `python /usr/local/share/get_selenium_url.py`

# Create the file for the hub_server, if a server name is provided
if [ -n "$1" ]; then
    echo $1 > /usr/local/share/hub_url
    stop selenium_node
    start selenium_node
fi

