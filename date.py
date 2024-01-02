import com.atlassian.jira.bc.issue.search.SearchService
import com.atlassian.jira.component.ComponentAccessor
import com.atlassian.jira.issue.ModifiedValue
import com.atlassian.jira.issue.fields.CustomField
import com.atlassian.jira.issue.util.DefaultIssueChangeHolder
import com.atlassian.jira.web.bean.PagerFilter

def searchService = ComponentAccessor.getComponentOfType(SearchService)
def user = ComponentAccessor.jiraAuthenticationContext.loggedInUser

def eventIssue = event.issue

if (eventIssue) {
    def epic = eventIssue.getEpic()

    if (epic) {
        // Handle Epic Issue
        def epicIssueKey = epic.getKey()

        // Step 1: Search for all issues linked to the Epic (assuming "Epic Link" is the link)
        def filter = "\"Epic Link\" = $epicIssueKey AND \"Deployment Zone\" = MEA"
        SearchService.ParseResult parseResult = searchService.parseQuery(user, filter)
        def results = searchService.search(user, parseResult.query, PagerFilter.unlimitedFilter)
        def issues = results.results

        log.warn("Total issues linked to $epicIssueKey: " + issues.size())

        // Step 2: Find the earliest start date and latest end date among linked child issues
        def startDateFieldId = "customfield_11600" // Replace with your actual start date field ID
        def endDateFieldId = "customfield_11601" // Replace with your actual end date field ID

        def earliestStartDate = null
        def latestEndDate = null

        issues.each { issue ->
            def startDateField = ComponentAccessor.customFieldManager.getCustomFieldObject(startDateFieldId)
            def endDateField = ComponentAccessor.customFieldManager.getCustomFieldObject(endDateFieldId)

            def childStartDate = issue.getCustomFieldValue(startDateField)
            def childEndDate = issue.getCustomFieldValue(endDateField)

            if (childStartDate && childStartDate instanceof Date) {
                if (earliestStartDate == null || childStartDate.after(earliestStartDate)) {
                    earliestStartDate = childStartDate
                }
            }

            if (childEndDate && childEndDate instanceof Date) {
                if (latestEndDate == null || childEndDate.after(latestEndDate)) {
                    latestEndDate = childEndDate
                }
            }
        }
       
       log.warn(earliestStartDate)
       log.warn(latestEndDate)
       
        // Step 3: Update the Epic issue's start and end date fields
        def epicIssue = ComponentAccessor.issueManager.getIssueByCurrentKey(epicIssueKey)
        log.warn(epicIssueKey)

        if (epicIssue) {
            def epicStartDateField = ComponentAccessor.customFieldManager.getCustomFieldObject("customfield_11600") // Replace with your actual epic start date field ID
            def epicEndDateField = ComponentAccessor.customFieldManager.getCustomFieldObject("customfield_11601") // Replace with your actual epic end date field ID

            if (epicStartDateField && epicEndDateField) {
                epicStartDateField.updateValue(null, epicIssue, new ModifiedValue(epicIssue.getCustomFieldValue(epicStartDateField), earliestStartDate), new DefaultIssueChangeHolder())
                epicEndDateField.updateValue(null, epicIssue, new ModifiedValue(epicIssue.getCustomFieldValue(epicEndDateField), latestEndDate), new DefaultIssueChangeHolder())
            }

            log.warn("Updated Start and End Date Fields on Epic $epicIssueKey.")
        } else {
            log.warn("Epic issue $epicIssueKey not found.")
        }
    }
} else {
    log.warn("The event issue is null.")
}
