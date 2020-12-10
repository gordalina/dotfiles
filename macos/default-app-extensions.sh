# configure default app for extensions
extensions=(js jsx ts tsx json ex exs csv yml yaml)
for ext in ${extensions[@]}; do
  duti -s com.microsoft.VSCode $ext all
done
