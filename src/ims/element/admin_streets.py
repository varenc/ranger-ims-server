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
Admin streets page.
"""

from .base import Element, renderer
from ..data.json import jsonTextFromObject

__all__ = (
    "AdminStreetsPage",
)



class AdminStreetsPage(Element):
    """
    Admin streets page.
    """

    def __init__(self, service):
        """
        @param service: The service.
        """
        Element.__init__(
            self, "admin_streets", service,
            title="Admin: Event Concentric Streets",
        )


    @renderer
    def eventNames(self, request, tag):
        """
        JSON list of events IDs.
        """
        return jsonTextFromObject(e.id for e in self.service.storage.events())