# configure default app for extensions
extensions=(js jsx ts tsx json ex exs csv)
for ext in ${extensions[@]}; do
  duti -s com.microsoft.VSCode $ext all
done
