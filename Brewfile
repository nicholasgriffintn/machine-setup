cask_args appdir: "/Applications"
tap "homebrew/cask"
tap "homebrew/cask-fonts"

brew "python"
brew "zsh"
brew "jq"
brew "coreutils"
brew "git"
brew "awscli"
brew "nvm"
brew "gh"

cask "font-fantasque-sans-mono-nerd-font"
cask "font-meslo-lg-nerd-font"
cask "font-fira-code"

cask "visual-studio-code" unless system "test -e /Applications/Visual\\ Studio\\ Code.app"
cask "google-chrome" unless system "test -e /Applications/Google\\ Chrome.app"
cask "firefox" unless system "test -e /Applications/Firefox.app"
cask "slack" unless system "test -e /Applications/Slack.app"