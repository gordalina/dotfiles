# create directories
mkdir -p ~/Audio/VST
mkdir -p ~/Audio/VST3

# Delete system folders
sudo rm -fr /Library/Audio/Plug-Ins/VST
sudo rm -fr /Library/Audio/Plug-Ins/VST3

# Link system folders to local audio
sudo ln -s /Library/Audio/Plug-Ins/VST ~/Audio/VST
sudo ln -s /Library/Audio/Plug-Ins/VST3 ~/Audio/VST3
