import com.atlassian.jira.bc.issue.search.SearchService
import com.atlassian.jira.component.ComponentAccessor
import com.atlassian.jira.issue.Issue
import com.atlassian.jira.web.bean.PagerFilter
 
def searchService = ComponentAccessor.getComponentOfType(SearchService)
def user = ComponentAccessor.jiraAuthenticationContext.loggedInUser
 
def eventIssue = event.issue
 
if (eventIssue) {
    def epic = eventIssue.getEpic()
   
    if (epic) {
        // Handle Epic Issue
       
        def epicIssueKey = epic.getKey()
 
        // Step 1: Search for all issues linked to the Epic (LTI-9)
        def filter = "\"Epic Link\" = $epicIssueKey"
        SearchService.ParseResult parseResult = searchService.parseQuery(user, filter)
        def results = searchService.search(user, parseResult.query, PagerFilter.unlimitedFilter)
        def issues = results.results
 
        log.warn("Total issues linked to $epicIssueKey: " + issues.size())
 
        // Step 2: Calculate the total time spent, estimate, and original estimate on linked issues
        def totalSpentTime = 0
        def totalEstimate = 0
        def totalOriginalEstimate = 0
 
        issues.each { issue ->
            def issueKey = issue.key
            def timeSpent = issue.getTimeSpent() ?: 0
            def estimate = issue.getEstimate() ?: 0
            def originalEstimate = issue.getOriginalEstimate() ?: 0
           
            totalSpentTime += timeSpent
            totalEstimate += estimate
            totalOriginalEstimate += originalEstimate
 
            log.warn("Issue Key: " + issueKey)
            log.warn("Time Spent on $issueKey: " + timeSpent)
            log.warn("Estimate on $issueKey: " + estimate)
            log.warn("Original Estimate on $issueKey: " + originalEstimate)
        }
 
        // Step 3: Update the Epic issue's fields with the calculated totals
        def epicIssue = ComponentAccessor.issueManager.getIssueByCurrentKey(epicIssueKey)
 
        if (epicIssue) {
            epicIssue.setTimeSpent(totalSpentTime)
            epicIssue.setEstimate(totalEstimate)
            epicIssue.setOriginalEstimate(totalOriginalEstimate)
            epicIssue.store() // Save the updated Epic issue
            log.warn("Updated Time Spent on Epic $epicIssueKey to: " + totalSpentTime)
            log.warn("Updated Estimate on Epic $epicIssueKey to: " + totalEstimate)
            log.warn("Updated Original Estimate on Epic $epicIssueKey to: " + totalOriginalEstimate)
        } else {
            log.warn("Epic issue $epicIssueKey not found.")
        }
    }
} else {
    log.warn("The event issue is null.")
}
