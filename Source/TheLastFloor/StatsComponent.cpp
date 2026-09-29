#include "StatsComponent.h"

UStatsComponent::UStatsComponent()
{
	// Nothing here needs per-frame work: the component pushes changes out
	// through OnStatsChanged instead of being polled.
	PrimaryComponentTick.bCanEverTick = false;
}

void UStatsComponent::ApplyDamage(int32 Amount)
{
	if (Amount <= 0)
	{
		return;
	}

	const int32 NewHealth = FMath::Max(0, Health - Amount);
	if (NewHealth == Health)
	{
		// Already dead; no state moved, so no reason to wake listeners.
		return;
	}

	Health = NewHealth;
	OnStatsChanged.Broadcast();
}

void UStatsComponent::AddEnergy(int32 Amount)
{
	const int32 NewEnergy = FMath::Clamp(Energy + Amount, 0, MaxEnergy);
	if (NewEnergy == Energy)
	{
		return;
	}

	Energy = NewEnergy;
	OnStatsChanged.Broadcast();
}

void UStatsComponent::AddCurrency(int32 Amount)
{
	const int32 NewCurrency = FMath::Max(0, Currency + Amount);
	if (NewCurrency == Currency)
	{
		return;
	}

	Currency = NewCurrency;
	OnStatsChanged.Broadcast();
}

void UStatsComponent::GoToNextFloor()
{
	++Floor;
	Energy = MaxEnergy;

	// One broadcast for both changes: listeners re-read everything anyway.
	OnStatsChanged.Broadcast();
}

float UStatsComponent::GetHealthFraction() const
{
	// MaxHealth is clamped to at least 1 in the editor, so this cannot divide by zero.
	return static_cast<float>(Health) / static_cast<float>(MaxHealth);
}

float UStatsComponent::GetEnergyFraction() const
{
	return static_cast<float>(Energy) / static_cast<float>(MaxEnergy);
}

bool UStatsComponent::IsLowHealth() const
{
	return GetHealthFraction() <= 0.25f;
}
