Unicode true
!include "MUI2.nsh"
!include "x64.nsh"
!include "WinVer.nsh"
!ifndef PF_ROOT
 !error "Pass /DPF_ROOT=source-root"
!endif
Name "PhœnixForge 1.7.0"
OutFile "${PF_ROOT}\dist\PhoenixForge_v1.7.0_Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\PhoenixForge"
RequestExecutionLevel user
SetCompressor /SOLID lzma
BrandingText "PhœnixForge — Forge Digital Logic"
!define MUI_ICON "${PF_ROOT}\app\assets\PhoenixForge.ico"
!define MUI_UNICON "${PF_ROOT}\app\assets\PhoenixForge.ico"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${PF_ROOT}\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Spanish"

Function .onInit
 ${IfNot} ${RunningX64}
  MessageBox MB_ICONSTOP "Esta edición requiere Windows de 64 bits."
  Abort
 ${EndIf}
 ${IfNot} ${AtLeastWin10}
  MessageBox MB_ICONSTOP "Esta edición requiere Windows 10 (1809 o posterior)."
  Abort
 ${EndIf}
 ReadRegStr $R0 HKLM "SOFTWARE\Microsoft\Windows NT\CurrentVersion" "CurrentBuildNumber"
 IntCmp $R0 17763 version_ok version_old version_ok
 version_old:
  MessageBox MB_ICONSTOP "Se requiere Windows build 17763 o posterior."
  Abort
 version_ok:
 SetShellVarContext current
FunctionEnd

Section "PhœnixForge (obligatorio)" Main
 SectionIn RO
 SetOutPath "$INSTDIR"
 File /oname=PhoenixForge.exe "${PF_ROOT}\dist\PhoenixForge_v1.7.0_Portable.exe"
 File "${PF_ROOT}\LICENSE"
 File "${PF_ROOT}\THIRD_PARTY_NOTICES.md"
 SetOutPath "$INSTDIR\docs"
 File /r "${PF_ROOT}\docs\*.*"
 SetOutPath "$INSTDIR\licenses"
 File /r "${PF_ROOT}\vendor\licenses\*.*"
 SetOutPath "$INSTDIR\sources"
 File "${PF_ROOT}\vendor\sources\*.*"
 SetOutPath "$INSTDIR"
 WriteUninstaller "$INSTDIR\Uninstall.exe"
 CreateDirectory "$SMPROGRAMS\PhoenixForge"
 CreateShortCut "$SMPROGRAMS\PhoenixForge\PhœnixForge.lnk" "$INSTDIR\PhoenixForge.exe"
 CreateShortCut "$SMPROGRAMS\PhoenixForge\Desinstalar.lnk" "$INSTDIR\Uninstall.exe"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\PhoenixForge" "DisplayName" "PhœnixForge"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\PhoenixForge" "DisplayVersion" "1.7.0"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\PhoenixForge" "DisplayIcon" "$INSTDIR\PhoenixForge.exe"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\PhoenixForge" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
 WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\PhoenixForge" "NoModify" 1
 WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\PhoenixForge" "NoRepair" 1
SectionEnd

Section /o "Acceso directo en el escritorio" Desktop
 CreateShortCut "$DESKTOP\PhœnixForge.lnk" "$INSTDIR\PhoenixForge.exe"
SectionEnd

Section "Uninstall"
 SetShellVarContext current
 Delete "$DESKTOP\PhœnixForge.lnk"
 Delete "$SMPROGRAMS\PhoenixForge\PhœnixForge.lnk"
 Delete "$SMPROGRAMS\PhoenixForge\Desinstalar.lnk"
 RMDir "$SMPROGRAMS\PhoenixForge"
 Delete "$INSTDIR\PhoenixForge.exe"
 Delete "$INSTDIR\LICENSE"
 Delete "$INSTDIR\THIRD_PARTY_NOTICES.md"
 Delete "$INSTDIR\Uninstall.exe"
 # Only owned application resources; never the user's PhoenixForge data folder.
 RMDir /r "$INSTDIR\docs"
 RMDir /r "$INSTDIR\licenses"
 RMDir /r "$INSTDIR\sources"
 RMDir "$INSTDIR"
 DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\PhoenixForge"
SectionEnd
