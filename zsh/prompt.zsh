autoload colors && colors

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
      if $(git_in_rebase)
      then
        rebase="%{$reset_color%} rebasing onto %{$fg_bold[magenta]%}$($git rev-parse --short HEAD)"
        echo "on %{$fg_bold[red]%}$(git_rebasing_branch)${rebase}%{$reset_color%}"
      else
        echo "on %{$fg_bold[red]%}$(git_prompt_info)%{$reset_color%}"
      fi
    fi
  fi
}

git_in_rebase() {
  test -d "$($git rev-parse --git-path rebase-merge 2>/dev/null)" || \
    test -d "$($git rev-parse --git-path rebase-apply 2>/dev/null)"
}

git_rebasing_branch() {
  for location in rebase-merge rebase-apply; do
    path=$($git rev-parse --git-path ${location})
    if test -d ${path}; then
      revision=$(<${path}/head-name)
      echo ${revision##refs/heads/}
      return 0
    fi
  done
}


git_prompt_info() {
  ref=$($git symbolic-ref HEAD 2>/dev/null) || return
  echo "${ref#refs/heads/}"
}

# This assumes that you always have an origin named `origin`, and that you only
# care about one specific origin. If this is not the case, you might want to use
# `$git cherry -v @{upstream}` instead.
need_push () {
  if [ $($git rev-parse --is-inside-work-tree 2>/dev/null) ]
  then
    number=$($git cherry -v origin/$(git symbolic-ref --short HEAD 2>/dev/null) 2>/dev/null | wc -l | bc)

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
  kubectl config current-context 2> /dev/null
}

kubernetes_namespace() {
  context=$(kubectl config current-context 2> /dev/null)
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

gcp_project() {
  gcloud config get-value project 2>/dev/null
}

gcp_prompt() {
  project=$(gcp_project)

  if [ "$project" != "" ]; then
    echo " gcp:%{$fg_bold[yellow]%}$project%{$reset_color%}"
  fi
}

prompt() {
  IN_PROMPT=" in "
  TOOLS_PROMPT="$(kubernetes_prompt)$(terraform_prompt)"

  if [ "${TOOLS_PROMPT}" = "" ]; then
    IN_PROMPT=""
  fi

  p_pr='%(?.%F{blue}.%F{red})>%f'


  echo "${TOOLS_PROMPT}${IN_PROMPT}$(directory_name) $(git_dirty)$(need_push)"
}

two_line_prompt() {
  echo "\n$(prompt)\n%(?.%F{white}.%F{red})›%f "
}

export PROMPT=$'$(two_line_prompt)'

set_prompt () {
  export RPROMPT="%{$fg_bold[cyan]%}%{$reset_color%}"
}

precmd() {
  title "zsh" "%m" "%55<...<%~"
  set_prompt
}
