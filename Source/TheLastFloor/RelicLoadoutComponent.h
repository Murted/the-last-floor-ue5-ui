#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "RelicLoadoutComponent.generated.h"

/** Broadcast after any equip slot changes. Listeners re-read every slot. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnLoadoutChanged);

/**
 * Which relics the player has equipped, by DT_Relics row name.
 *
 * Lives on the player controller rather than in the relics screen, because the
 * screen is destroyed every time the player leaves it. The screen only shows
 * this state and asks for changes; the rules (fixed slot count, a relic can sit
 * in one slot only) are enforced here, so no widget can break them.
 */
UCLASS(ClassGroup = (TheLastFloor), meta = (BlueprintSpawnableComponent))
class THELASTFLOOR_API URelicLoadoutComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	URelicLoadoutComponent();

	/** How many equip slots the screen shows. */
	static constexpr int32 NumSlots = 3;

	/** Fires after any slot has changed. */
	UPROPERTY(BlueprintAssignable, Category = "Relics")
	FOnLoadoutChanged OnLoadoutChanged;

	/** Row name of the relic in the slot, or None if the slot is empty or the index is out of range. */
	UFUNCTION(BlueprintPure, Category = "Relics")
	FName GetRelicInSlot(int32 SlotIndex) const;

	/** Index of the slot holding this relic, or -1 if it is not equipped. */
	UFUNCTION(BlueprintPure, Category = "Relics")
	int32 FindSlotOfRelic(FName RelicId) const;

	UFUNCTION(BlueprintPure, Category = "Relics")
	int32 GetNumSlots() const { return NumSlots; }

	/**
	 * Puts a relic into a slot. A relic can be equipped only once: if it already
	 * sits in another slot, the two slots swap contents, so dragging between
	 * slots moves the relic and whatever was in the target goes to its old place.
	 * Passing None empties the slot.
	 */
	UFUNCTION(BlueprintCallable, Category = "Relics")
	void EquipRelic(int32 SlotIndex, FName RelicId);

	/** Empties a slot. Does nothing if it is already empty. */
	UFUNCTION(BlueprintCallable, Category = "Relics")
	void UnequipSlot(int32 SlotIndex);

private:
	/** One entry per slot; NAME_None means empty. Always exactly NumSlots long. */
	UPROPERTY(VisibleInstanceOnly, Category = "Relics")
	TArray<FName> EquippedRelics;
};
