#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "StatsComponent.generated.h"

/**
 * Broadcast whenever any stat changes. Dynamic so Blueprints can bind to it,
 * multicast so several listeners (HUD, audio, analytics) can share one source.
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnStatsChanged);

/**
 * Run stats for a single tower climb: health, energy, currency and floor.
 *
 * Every stat is read-only to Blueprints and can only be changed through the
 * functions below, each of which broadcasts OnStatsChanged. That makes it
 * impossible to move a stat without the HUD hearing about it.
 */
UCLASS(ClassGroup = (TheLastFloor), meta = (BlueprintSpawnableComponent))
class THELASTFLOOR_API UStatsComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UStatsComponent();

	/** Fires after any stat has changed. Listeners re-read what they display. */
	UPROPERTY(BlueprintAssignable, Category = "Stats")
	FOnStatsChanged OnStatsChanged;

	// --- Current values: read-only, moved only through the functions below ---

	UPROPERTY(BlueprintReadOnly, Category = "Stats|Health")
	int32 Health = 100;

	UPROPERTY(BlueprintReadOnly, Category = "Stats|Energy")
	int32 Energy = 50;

	UPROPERTY(BlueprintReadOnly, Category = "Stats|Progress")
	int32 Currency = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Stats|Progress")
	int32 Floor = 1;

	// --- Limits: tunable per instance in the editor ---

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Stats|Health", meta = (ClampMin = "1"))
	int32 MaxHealth = 100;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Stats|Energy", meta = (ClampMin = "1"))
	int32 MaxEnergy = 50;

	// --- Mutators. Each one clamps, then broadcasts. ---

	/** Removes health, floored at zero. Negative amounts are ignored. */
	UFUNCTION(BlueprintCallable, Category = "Stats")
	void ApplyDamage(int32 Amount);

	/** Adds or spends energy; the result stays within [0, MaxEnergy]. */
	UFUNCTION(BlueprintCallable, Category = "Stats")
	void AddEnergy(int32 Amount);

	/** Adds or spends currency; the result never drops below zero. */
	UFUNCTION(BlueprintCallable, Category = "Stats")
	void AddCurrency(int32 Amount);

	/** Advances one floor and refills energy, the way a new floor should feel. */
	UFUNCTION(BlueprintCallable, Category = "Stats")
	void GoToNextFloor();

	/**
	 * Puts every stat back to the start of a climb: full health and energy,
	 * no currency, floor 1. The component outlives screens, so a new run has
	 * to reset it explicitly or it would continue the previous one.
	 */
	UFUNCTION(BlueprintCallable, Category = "Stats")
	void ResetRun();

	// --- Derived values the HUD asks for rather than computing itself ---

	/** Health as 0..1, ready for a progress bar. */
	UFUNCTION(BlueprintPure, Category = "Stats")
	float GetHealthFraction() const;

	/** Energy as 0..1, ready for a progress bar. */
	UFUNCTION(BlueprintPure, Category = "Stats")
	float GetEnergyFraction() const;

	/** True once health is at or below a quarter, which drives the low-health pulse. */
	UFUNCTION(BlueprintPure, Category = "Stats")
	bool IsLowHealth() const;
};
