{{/*
Expand the name of the chart.
*/}}
{{- define "openstack-actions-runner.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "openstack-actions-runner.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "openstack-actions-runner.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "openstack-actions-runner.labels" -}}
helm.sh/chart: {{ include "openstack-actions-runner.chart" . }}
{{ include "openstack-actions-runner.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "openstack-actions-runner.selectorLabels" -}}
app.kubernetes.io/name: {{ include "openstack-actions-runner.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "openstack-actions-runner.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "openstack-actions-runner.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
List secrets variables from values
*/}}
{{- define "helpers.list-env-variables"}}
{{- range $key, $val := .Values.env.secret }}
- name: {{ $key }}
  valueFrom:
    secretKeyRef:
      name: app-env-secret
      key: {{ $key }}
{{- end }}
{{- end }}
