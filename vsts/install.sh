mkdir -p ~/Google\ Drive/Audio/VST
mkdir -p ~/Google\ Drive/Audio/VST3
sudo rm -fr /Library/Audio/Plug-Ins/VST
sudo rm -fr /Library/Audio/Plug-Ins/VST3
sudo ln -s ~/Google\ Drive/Audio/VST /Library/Audio/Plug-Ins/VST
sudo ln -s ~/Google\ Drive/Audio/VST3 /Library/Audio/Plug-Ins/VST3
