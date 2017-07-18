##
# See the file COPYRIGHT for copyright information.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##

"""
Tests for :mod:`ranger-ims-server.store.sqlite._store`
"""

from collections import defaultdict
from datetime import datetime as DateTime, timedelta as TimeDelta
from typing import Any, Dict, Set, Tuple

from attr import fields as attrFields

from hypothesis import assume, given
from hypothesis.strategies import text, tuples

from ims.ext.sqlite import SQLITE_MAX_INT
from ims.model import (
    Event, Incident, IncidentPriority, IncidentState, RodGarettAddress
)
from ims.model.strategies import (
    concentricStreetIDs, incidentPriorities, incidentStates, incidentSummaries,
    incidents, locationNames, radialHours, radialMinutes, rangerHandles,
)

from .base import DataStoreTests

Dict, Event, Set  # silence linter


__all__ = ()



class DataStoreIncidentTests(DataStoreTests):
    """
    Tests for :class:`DataStore` incident access.
    """

    @given(tuples(incidents()))
    def test_incidents(self, incidents: Tuple[Incident]) -> None:
        """
        :meth:`DataStore.incidents` returns all incidents.
        """
        events: Dict[Event, Dict[int, Incident]] = defaultdict(defaultdict)

        store = self.store()

        for incident in incidents:
            assume(incident.number <= SQLITE_MAX_INT)
            assume(incident.number not in events[incident.event])

            self.storeIncident(store, incident)

            events[incident.event][incident.number] = incident

        for event in events:
            for retrieved in self.successResultOf(
                store.incidents(event)
            ):
                self.assertIncidentsEqual(
                    retrieved, events[incident.event][retrieved.number]
                )


    @given(incidents())
    def test_incidentWithNumber(self, incident: Incident) -> None:
        """
        :meth:`DataStore.incidentWithNumber` return the specified incident.
        """
        assume(incident.number <= SQLITE_MAX_INT)

        store = self.store()

        self.storeIncident(store, incident)

        retrieved = self.successResultOf(
            store.incidentWithNumber(incident.event, incident.number)
        )

        self.assertIncidentsEqual(retrieved, incident)


    @given(incidents(new=True), rangerHandles())
    def test_createIncident(self, incident: Incident, author: str) -> None:
        """
        :meth:`DataStore.createIncident` creates the given incident.
        """
        store = self.store()

        self.successResultOf(store.createEvent(incident.event))

        for incidentType in incident.incidentTypes:
            self.successResultOf(store.createIncidentType(incidentType))

        address = incident.location.address
        if (
            isinstance(address, RodGarettAddress) and
            address.concentric is not None
        ):
            self.successResultOf(
                store.createConcentricStreet(
                    incident.event, address.concentric, "Sesame Street"
                )
            )

        # The returned incident should be the same, except for modified number
        returnedIncident = self.successResultOf(
            store.createIncident(incident=incident, author=author)
        )
        self.assertIncidentsEqual(
            returnedIncident.replace(number=0), incident, True
        )
        self.assertNotEqual(returnedIncident.number, 0)

        # Stored incidents should be contain only the returned incident above
        storedIncidents = tuple(
            self.successResultOf(store.incidents(event=incident.event))
        )
        self.assertEqual(len(storedIncidents), 1)
        self.assertIncidentsEqual(storedIncidents[0], returnedIncident)


    def _test_setIncidentAttribute(
        self, incident: Incident,
        methodName: str, attributeName: str, value: Any
    ) -> None:
        store = self.store()

        self.storeIncident(store, incident)

        setter = getattr(store, methodName)

        # For concentric streets, we need to make sure they exist first.
        if attributeName == "location.address.concentric":
            self.storeConcentricStreet(
                store._db, incident.event, value, "Concentric Street",
                ignoreDuplicates=True,
            )

        self.successResultOf(
            setter(incident.event, incident.number, value, "Hubcap")
        )

        retrieved = self.successResultOf(
            store.incidentWithNumber(incident.event, incident.number)
        )

        # Normalize location if we're updating the address.
        if attributeName.startswith("location.address."):
            incident = self.normalizeAddress(incident)

        # Replace the specified incident attribute with the given value.
        # This is a bit complex because we're recursing into sub-attributes.
        attrPath = attributeName.split(".")
        values = [incident]
        for a in attrPath[:-1]:
            values.append(getattr(values[-1], a))
        values.append(value)
        for a in reversed(attrPath):
            v = values.pop()
            values[-1] = values[-1].replace(**{a: v})
        incident = values[0]

        self.assertIncidentsEqual(retrieved, incident, ignoreInitial=True)


    @given(incidents(new=True), incidentPriorities())
    def test_setIncidentPriority(
        self, incident: Incident, priority: IncidentPriority
    ) -> None:
        """
        :meth:`DataStore.setIncidentPriority` updates the priority for the
        incident with the given number in the data store.
        """
        self._test_setIncidentAttribute(
            incident, "setIncidentPriority", "priority", priority
        )


    @given(incidents(new=True), incidentStates())
    def test_setIncidentState(
        self, incident: Incident, state: IncidentState
    ) -> None:
        """
        :meth:`DataStore.setIncidentState` updates the state for the incident
        with the given number in the data store.
        """
        self._test_setIncidentAttribute(
            incident, "setIncidentState", "state", state
        )


    @given(incidents(new=True), incidentSummaries())
    def test_setIncidentSummary(
        self, incident: Incident, summary: str
    ) -> None:
        """
        :meth:`DataStore.setIncidentSummary` updates the summary for the
        incident with the given number in the data store.
        """
        self._test_setIncidentAttribute(
            incident, "setIncidentSummary", "summary", summary
        )


    @given(incidents(new=True), locationNames())
    def test_setIncidentLocationName(
        self, incident: Incident, name: str
    ) -> None:
        """
        :meth:`DataStore.setIncidentLocationName` updates the location name for
        the incident with the given number in the data store.
        """
        self._test_setIncidentAttribute(
            incident, "setIncidentLocationName", "location.name", name
        )


    @given(incidents(new=True), concentricStreetIDs())
    def test_setIncidentLocationConcentricStreet(
        self, incident: Incident, streetID: str
    ) -> None:
        """
        :meth:`DataStore.setIncidentLocationConcentricStreet` updates the
        location concentric street for the incident with the given number in
        the data store.
        """
        self._test_setIncidentAttribute(
            incident, "setIncidentLocationConcentricStreet",
            "location.address.concentric", streetID,
        )


    @given(incidents(new=True), radialHours())
    def test_setIncidentLocationRadialHour(
        self, incident: Incident, radialHour: int
    ) -> None:
        """
        :meth:`DataStore.setIncidentLocationRadialHour` updates the location
        radial hour for the incident with the given number in the data store.
        """
        self._test_setIncidentAttribute(
            incident, "setIncidentLocationRadialHour",
            "location.address.radialHour", radialHour,
        )


    @given(incidents(new=True), radialMinutes())
    def test_setIncidentLocationRadialMinute(
        self, incident: Incident, radialMinute: int
    ) -> None:
        """
        :meth:`DataStore.setIncidentLocationRadialMinute` updates the location
        radial minute for the incident with the given number in the data store.
        """
        self._test_setIncidentAttribute(
            incident, "setIncidentLocationRadialMinute",
            "location.address.radialMinute", radialMinute,
        )


    @given(incidents(new=True), text())
    def test_setIncidentLocationDescription(
        self, incident: Incident, description: str
    ) -> None:
        """
        :meth:`DataStore.setIncidentLocationDescription` updates the location
        description for the incident with the given number in the data store.
        """
        self._test_setIncidentAttribute(
            incident, "setIncidentLocationDescription",
            "location.address.description", description,
        )


    def assertIncidentsEqual(
        self, incidentA: Incident, incidentB: Incident,
        ignoreInitial: bool = False,
    ) -> None:
        if incidentA != incidentB:
            messages = []

            for attribute in attrFields(Incident):
                name = attribute.name
                valueA = getattr(incidentA, name)
                valueB = getattr(incidentB, name)

                if name == "created":
                    if dateTimesEqualish(valueA, valueB):
                        continue
                    else:
                        messages.append(
                            "{name} delta: {delta}"
                            .format(name=name, delta=valueA - valueB)
                        )

                if name == "reportEntries":
                    if ignoreInitial:
                        # Remove automatic entries
                        _valueA = tuple(e for e in valueA if not e.automatic)

                        if _valueA == valueA:
                            self.fail("No initial report entries found.")

                        valueA = _valueA

                    if len(valueA) == len(valueB):
                        for entryA, entryB in zip(valueA, valueB):
                            if entryA != entryB:
                                if entryA.author != entryB.author:
                                    break
                                if entryA.automatic != entryB.automatic:
                                    break
                                if entryA.text != entryB.text:
                                    break
                                if not dateTimesEqualish(
                                    entryA.created, entryB.created
                                ):
                                    break
                        else:
                            continue

                if valueA != valueB:
                    messages.append(
                        "{name} {valueA!r} != {valueB!r}"
                        .format(name=name, valueA=valueA, valueB=valueB)
                    )

            if messages:
                self.fail("Incidents do not match:\n" + "\n".join(messages))



def dateTimesEqualish(a: DateTime, b: DateTime) -> bool:
    """
    Compare two :class:`DateTimes`.
    Because floating point math, apply some "close enough" logic.
    """
    return a - b < TimeDelta(microseconds=20)
