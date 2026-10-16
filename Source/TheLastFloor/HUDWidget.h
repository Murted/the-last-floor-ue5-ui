#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "HUDWidget.generated.h"

// Pointers only, so the names are enough here; the real headers are included
// in the .cpp. Keeps this header cheap for everything that includes it.
class UProgressBar;
class UStatsComponent;
class UTextBlock;

/**
 * Base class for the in-run HUD.
 *
 * The widgets below are bound by name to whatever the designer built in
 * WBP_HUD: if one is missing or has the wrong type, the Widget Blueprint
 * refuses to compile. That turns the C++/designer contract into a
 * compile-time check rather than a runtime surprise.
 *
 * Abstract on purpose: this class has no widget tree of its own and is only
 * useful as the parent of a Widget Blueprint.
 */
UCLASS(Abstract)
class THELASTFLOOR_API UHUDWidget : public UUserWidget
{
	GENERATED_BODY()

protected:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;

	// --- Bound widgets. Names must match WBP_HUD exactly. ---

	UPROPERTY(meta = (BindWidget))
	TObjectPtr<UProgressBar> Bar_Health;

	UPROPERTY(meta = (BindWidget))
	TObjectPtr<UProgressBar> Bar_Energy;

	UPROPERTY(meta = (BindWidget))
	TObjectPtr<UTextBlock> Txt_Currency;

	UPROPERTY(meta = (BindWidget))
	TObjectPtr<UTextBlock> Txt_Floor;

	/** Shown only while health is low; animated in a later pass. */
	UPROPERTY(meta = (BindWidget))
	TObjectPtr<UTextBlock> Txt_ThreatBanner;

	/**
	 * Pushes every stat into the bound widgets.
	 * BlueprintCallable so the designer side can force a refresh if needed.
	 */
	UFUNCTION(BlueprintCallable, Category = "HUD")
	void RefreshFromStats();

	/** The stats this HUD mirrors. Found on the owning player controller. */
	UPROPERTY(BlueprintReadOnly, Transient, Category = "HUD")
	TObjectPtr<UStatsComponent> Stats;

	/**
	 * Fires only when health crosses the low threshold, in either direction.
	 * C++ decides *when* this happens; WBP_HUD decides what it looks like.
	 * No C++ body: UHT generates one that calls into the Blueprint, and does
	 * nothing if the Blueprint does not implement the event.
	 */
	UFUNCTION(BlueprintImplementableEvent, Category = "HUD")
	void OnLowHealthChanged(bool bIsLow);

private:
	/** Bound to UStatsComponent::OnStatsChanged; UFUNCTION is required for that. */
	UFUNCTION()
	void HandleStatsChanged();

	/** Low-health state at the previous refresh, so only transitions are reported. */
	bool bWasLowHealth = false;
};
