autoload colors && colors
# cheers, @ehrenmurdick
# http://github.com/ehrenmurdick/config/blob/master/zsh/prompt.zsh

if (( $+commands[git] ))
then
  git="$commands[git]"
else
  git="/usr/bin/git"
fi

git_branch() {
  echo $($git symbolic-ref HEAD 2>/dev/null | awk -F/ {'print $NF'})
}

git_dirty() {
  if $(! $git status -s &> /dev/null)
  then
    echo ""
  else
    if [[ $($git status --porcelain) == "" ]]
    then
      echo "on %{$fg_bold[green]%}$(git_prompt_info)%{$reset_color%}"
    else
      echo "on %{$fg_bold[red]%}$(git_prompt_info)%{$reset_color%}"
    fi
  fi
}

git_prompt_info () {
 ref=$($git symbolic-ref HEAD 2>/dev/null) || return
# echo "(%{\e[0;33m%}${ref#refs/heads/}%{\e[0m%})"
 echo "${ref#refs/heads/}"
}

# This assumes that you always have an origin named `origin`, and that you only
# care about one specific origin. If this is not the case, you might want to use
# `$git cherry -v @{upstream}` instead.
need_push () {
  if [ $($git rev-parse --is-inside-work-tree 2>/dev/null) ]
  then
    number=$($git cherry -v origin/$(git symbolic-ref --short HEAD) 2>/dev/null | wc -l | bc)

    if [[ $number == 0 ]]
    then
      echo " "
    else
      echo " with %{$fg_bold[magenta]%}$number unpushed%{$reset_color%}"
    fi
  fi
}

directory_name() {
  echo "%{$fg_bold[cyan]%}%1/%\/%{$reset_color%}"
}

battery_status() {
  if [[ $(sysctl -n hw.model) == *"Book"* ]]
  then
    $ZSH/bin/battery-status
  fi
}

kubernetes_context() {
  kubectl config current-context
}

kubernetes_namespace() {
  context=$(kubectl config current-context)
  namespace=$(kubectl config view -o jsonpath="{.contexts[?(@.name == \"$context\")].context.namespace}")

  if [ "$namespace" = "" ] || [ "$namespace" = "default" ]; then
    namespace=""
  else
    namespace=":${namespace}"
  fi

  echo $namespace
}

kubernetes_prompt() {
  if [[ "$PS1_DISABLE_KUBERNETES" != "yes" ]]; then;
    echo "%{$fg_bold[green]%}$(kubernetes_context)$(kubernetes_namespace)%{$reset_color%}"
  fi
}

terraform_workspace() {
  terraform workspace show 2>/dev/null
}

terraform_prompt() {
  ws=$(terraform_workspace)

  if [ "$ws" != "default" ] && [ "$ws" != "" ]; then
    echo " tf:%{$fg_bold[yellow]%}$ws%{$reset_color%}"
  fi
}

prompt() {
  K8S_PROMPT=$(kubernetes_prompt)
  TERRAFORM_PROMPT=$(terraform_prompt)
  IN_PROMPT=" in "

  if [[ "$K8S_PROMPT" == "" ]] && [[ "$TERRAFORM_PROMPT" == "" ]]; then
    IN_PROMPT=""
  fi

  echo "${K8S_PROMPT}${TERRAFORM_PROMPT}${IN_PROMPT}$(directory_name) $(git_dirty)$(need_push)"
}

export PROMPT=$'\n$(prompt)\n› '

set_prompt () {
  export RPROMPT="%{$fg_bold[cyan]%}%{$reset_color%}"
}

precmd() {
  title "zsh" "%m" "%55<...<%~"
  set_prompt
}
