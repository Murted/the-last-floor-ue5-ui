#include "RelicLoadoutComponent.h"

URelicLoadoutComponent::URelicLoadoutComponent()
{
	// Changes are pushed through OnLoadoutChanged; nothing to do per frame.
	PrimaryComponentTick.bCanEverTick = false;

	EquippedRelics.Init(NAME_None, NumSlots);
}

FName URelicLoadoutComponent::GetRelicInSlot(int32 SlotIndex) const
{
	// Out-of-range reads look like an empty slot, so a misconfigured widget
	// shows nothing instead of crashing.
	return EquippedRelics.IsValidIndex(SlotIndex) ? EquippedRelics[SlotIndex] : NAME_None;
}

int32 URelicLoadoutComponent::FindSlotOfRelic(FName RelicId) const
{
	if (RelicId.IsNone())
	{
		return INDEX_NONE;
	}
	return EquippedRelics.Find(RelicId);
}

void URelicLoadoutComponent::EquipRelic(int32 SlotIndex, FName RelicId)
{
	if (!EquippedRelics.IsValidIndex(SlotIndex))
	{
		UE_LOG(LogTemp, Warning, TEXT("URelicLoadoutComponent: slot %d is out of range (0..%d)."),
			SlotIndex, NumSlots - 1);
		return;
	}

	if (EquippedRelics[SlotIndex] == RelicId)
	{
		// Dropped onto the slot it is already in: nothing moved, nobody to wake.
		return;
	}

	// One relic, one slot: if it is equipped elsewhere, that slot takes what
	// the target slot held (possibly None). This turns slot-to-slot drags into
	// swaps and grid-to-slot drags of an equipped relic into moves.
	const int32 PreviousSlot = FindSlotOfRelic(RelicId);
	if (PreviousSlot != INDEX_NONE)
	{
		EquippedRelics[PreviousSlot] = EquippedRelics[SlotIndex];
	}

	EquippedRelics[SlotIndex] = RelicId;

	// One broadcast even when two slots changed: listeners re-read all slots.
	OnLoadoutChanged.Broadcast();
}

void URelicLoadoutComponent::UnequipSlot(int32 SlotIndex)
{
	if (!EquippedRelics.IsValidIndex(SlotIndex) || EquippedRelics[SlotIndex].IsNone())
	{
		return;
	}

	EquippedRelics[SlotIndex] = NAME_None;
	OnLoadoutChanged.Broadcast();
}
