{{/*
Define ports for the pods
*/}}
{{- define "chart.container-port" -}}
{{-  default "8000" .Values.servingEngineSpec.containerPort }}
{{- end }}

{{/*
Define service port
*/}}
{{- define "chart.service-port" -}}
{{-  if .Values.servingEngineSpec.servicePort }}
{{-    .Values.servingEngineSpec.servicePort }}
{{-  else }}
{{-    include "chart.container-port" . }}
{{-  end }}
{{- end }}

{{/*
Define service port name
*/}}
{{- define "chart.service-port-name" -}}
"service-port"
{{- end }}

{{/*
Define container port name
*/}}
{{- define "chart.container-port-name" -}}
"container-port"
{{- end }}

{{/*
Define deployment strategy
*/}}
{{- define "chart.strategy" -}}
strategy:
  rollingUpdate:
    maxSurge: 100%
    maxUnavailable: 0
{{- end }}

{{/*
Define additional ports
*/}}
{{- define "chart.extraPorts" }}
{{-   with .Values.servingEngineSpec.extraPorts }}
{{      toYaml . }}
{{-   end }}
{{- end }}


{{/*
Define liveness et readiness probes
*/}}
{{- define "chart.probes" -}}
{{-   if .Values.servingEngineSpec.readinessProbe  }}
readinessProbe:
{{-     with .Values.servingEngineSpec.readinessProbe }}
{{-       toYaml . | nindent 2 }}
{{-     end }}
{{-   end }}
{{-   if .Values.servingEngineSpec.livenessProbe  }}
livenessProbe:
{{-     with .Values.servingEngineSpec.livenessProbe }}
{{-       toYaml . | nindent 2 }}
{{-     end }}
{{-   end }}
{{- end }}

{{/*
Define resources
*/}}
{{- define "chart.resources" -}}
requests:
  memory: {{ required "Value 'resources.requests.memory' must be defined !" .Values.servingEngineSpec.resources.requests.memory | quote }}
  cpu: {{ required "Value 'resources.requests.cpu' must be defined !" .Values.servingEngineSpec.resources.requests.cpu | quote }}
  {{- if and (gt (int (index .Values.servingEngineSpec.resources.requests "nvidia.com/gpu")) 0) (gt (int (index .Values.servingEngineSpec.resources.limits "nvidia.com/gpu")) 0) }}
  nvidia.com/gpu: {{ required "Value 'resources.requests.nvidia.com/gpu' must be defined !" (index .Values.servingEngineSpec.resources.requests "nvidia.com/gpu") | quote }}
  {{- end }}
limits:
  memory: {{ required "Value 'resources.limits.memory' must be defined !" .Values.servingEngineSpec.resources.limits.memory | quote }}
  cpu: {{ required "Value 'resources.limits.cpu' must be defined !" .Values.servingEngineSpec.resources.limits.cpu | quote }}
  {{- if and (gt (int (index .Values.servingEngineSpec.resources.requests "nvidia.com/gpu")) 0) (gt (int (index .Values.servingEngineSpec.resources.limits "nvidia.com/gpu")) 0) }}
  nvidia.com/gpu: {{ required "Value 'resources.limits.nvidia.com/gpu' must be defined !" (index .Values.servingEngineSpec.resources.limits "nvidia.com/gpu") | quote }}
  {{- end }}
{{- end }}


{{/*
Define User used for the main container
*/}}
{{- define "chart.user" }}
{{-   if .Values.servingEngineSpec.image.runAsUser  }}
runAsUser: 
{{-     with .Values.servingEngineSpec.runAsUser }}
{{-       toYaml . | nindent 2 }}
{{-     end }}
{{-   end }}
{{- end }}

{{/*
  Define labels for serving engine and its service
*/}}
{{- define "chart.engineLabels" -}}
{{-   with .Values.servingEngineSpec.labels -}}
{{      toYaml . }}
{{-   end }}
{{- end }}

{{/*
  Define labels for router and its service
*/}}
{{- define "chart.routerLabels" -}}
{{-   with .Values.routerSpec.labels -}}
{{      toYaml . }}
{{-   end }}
{{- end }}

{{/*
  Define helper function to convert labels to a comma separated list
*/}}
{{- define "labels.toCommaSeparatedList" -}}
{{- $labels := . -}}
{{- $result := "" -}}
{{- range $key, $value := $labels -}}
  {{- if $result }},{{ end -}}
  {{ $key }}={{ $value }}
  {{- $result = "," -}}
{{- end -}}
{{- end -}}
