#!/usr/bin/env pwsh
#Requires -Version 6

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

Set-PSRepository -Name PSGallery -InstallationPolicy Trusted
Install-Module -Name PSScriptAnalyzer -RequiredVersion 1.17.1

# Installed the PSCustomUseLiteralPath rule
Install-Module -Name PSSA-PSCustomUseLiteralPath -RequiredVersion 0.1.1
