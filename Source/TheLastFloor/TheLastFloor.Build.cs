// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class TheLastFloor : ModuleRules
{
	public TheLastFloor(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
	
		// UMG — публичная зависимость: UUserWidget, UProgressBar и meta=(BindWidget)
		// появляются в наших заголовках (UHUDWidget.h), а не только в .cpp.
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore", "EnhancedInput", "UMG" });

		// Slate/SlateCore — слой под UMG. Пока нужны только внутри .cpp, поэтому private.
		// Если в заголовке появится FSlateBrush/FSlateColor — SlateCore переедет в public.
		PrivateDependencyModuleNames.AddRange(new string[] { "Slate", "SlateCore" });

		// Uncomment if you are using online features
		// PrivateDependencyModuleNames.Add("OnlineSubsystem");

		// To include OnlineSubsystemSteam, add it to the plugins section in your uproject file with the Enabled attribute set to true
	}
}
