#!/bin/zsh

TEMPORARY_DIR=temp-gula

# Split the first argument into an array of requested modules
REQUESTED_MODULES=("$@")

# Loop over each module name in the REQUESTED_MODULES array
for MODULE_NAME in "${REQUESTED_MODULES[@]}"; do
  matches=$(find ./"$TEMPORARY_DIR"/dist -type f -name "*.tar.gz" | grep "$MODULE_NAME")
  if [ -n "$matches" ]; then
    mv "$matches" .
    echo "Archivo para el paquete $MODULE_NAME copiado correctamente en root"
  else
    echo "Archivo no encontrado para el paquete: $MODULE_NAME"
  fi
done
