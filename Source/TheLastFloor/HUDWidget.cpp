#include "HUDWidget.h"

#include "Components/ProgressBar.h"
#include "Components/TextBlock.h"
#include "GameFramework/PlayerController.h"
#include "StatsComponent.h"

#define LOCTEXT_NAMESPACE "HUD"

void UHUDWidget::NativeConstruct()
{
	Super::NativeConstruct();

	// By now the widget tree exists, the BindWidget pointers are filled and the
	// owning player is available — none of which is true in the constructor.
	if (const APlayerController* Owner = GetOwningPlayer())
	{
		Stats = Owner->FindComponentByClass<UStatsComponent>();
	}

	if (!Stats)
	{
		// Better a loud log line than a HUD that silently shows nothing.
		UE_LOG(LogTemp, Warning,
			TEXT("UHUDWidget: no UStatsComponent on the owning player controller; "
				 "the HUD will stay empty."));
		return;
	}

	Stats->OnStatsChanged.AddDynamic(this, &UHUDWidget::HandleStatsChanged);

	// The delegate only fires on change, so paint the current values once.
	RefreshFromStats();
}

void UHUDWidget::NativeDestruct()
{
	// NativeConstruct runs every time the widget is added to the viewport, so
	// the unsubscribe has to mirror it. Without this, a widget that is removed
	// and re-added would end up handling every change twice.
	if (Stats)
	{
		Stats->OnStatsChanged.RemoveDynamic(this, &UHUDWidget::HandleStatsChanged);
	}

	Super::NativeDestruct();
}

void UHUDWidget::HandleStatsChanged()
{
	RefreshFromStats();
}

void UHUDWidget::RefreshFromStats()
{
	if (!Stats)
	{
		return;
	}

	// ProgressBar wants a 0..1 fraction; the component does the division so the
	// widget never has to know about MaxHealth.
	Bar_Health->SetPercent(Stats->GetHealthFraction());
	Bar_Energy->SetPercent(Stats->GetEnergyFraction());

	// AsNumber, not FString::FromInt: it applies the viewer's locale, so a
	// thousands separator comes out right without any work here.
	Txt_Currency->SetText(FText::AsNumber(Stats->Currency));

	// Format instead of concatenation, because the placeholder can move inside
	// the sentence when the text is translated.
	Txt_Floor->SetText(FText::Format(
		LOCTEXT("FloorFormat", "FLOOR {0}"),
		FText::AsNumber(Stats->Floor)));

	const bool bShowThreat = Stats->IsLowHealth();
	Txt_ThreatBanner->SetText(LOCTEXT("ThreatBanner", "DANGER"));
	// Collapsed rather than Hidden: a collapsed widget takes no layout space.
	Txt_ThreatBanner->SetVisibility(
		bShowThreat ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
}

#undef LOCTEXT_NAMESPACE
