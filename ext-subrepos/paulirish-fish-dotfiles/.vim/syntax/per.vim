" AOE2 AI-scripting vim syntax highlighting file
"
" by Silverweed91
" Jun 2014

if exists("b:current_syntax")
	finish
endif

"" Facts
syn match perNumber /[0-9]\+/
syn match perString /"[^"]*"/
syn keyword perConstantFacts true false 
syn match perEventDetectionFacts /\(event-detected\|taunt-detected\|timer-triggered\)/
syn match perGameFacts /\(cheats-enabled\|death-match-game\|difficulty\|game-time\|map-size\|map-type\|player-computer\|player-human\|player-in-game\|player-resigned\|player-valid\|population-cap\|regicide-game\|starting-age\|starting-resources\|victory-condition\)/ 
syn match perCommodityTradeFacts /\(can-buy-commodity\|can-sell-commodity\|commodity-buying-price\|commodity-selling-price\)/ 
syn match perTributeDetectionFacts /\(players-tribute\|players-tribute-memory\)/
syn match perEscrowFacts /\(can-build-gate-with-escrow\|can-build-wall-with-escrow\|can-build-with-escrow\|can-research-with-escrow\|can-spy-with-escrow\|can-train-with-escrow\|escrow-amount\)/
syn match perComputerPlayerObjectCountFacts /\(attack-soldier-count\|attack-boat-count\|building-count\|building-count-total\|building-type-count\|building-type-count-total\|civilian-population\|defend-soldier-count\|defend-warboat-count\|housing-headroom\|idle-farm-count\|military-population\|population\|population-headroom\|soldier-count\|unit-count\|unit-count-total\|unit-type-count\|unit-type-count-total\|warboat-count\)/ 
syn match perComputerPlayerResourceFacts /\(dropsite-min-distance\|food-amount\|gold-amount\|resource-found\|sheep-and-forage-too-far\|stone-amount\|wood-amount\)/
syn match perRegicideFacts /\(can-spy\)/
syn match perComputerPlayerAvailabilityFacts /\(building-available\|can-afford-building\|can-afford-complete-wall\|can-afford-research\|can-afford-unit\|can-build\|can-build-gate\|can-build-wall\|can-research\|can-train\|research-available\|research-completed\|unit-available\|wall-completed-percentage\|wall-invisible-percentage\)/ 
syn match perComputerPlayerMiscellaneousFacts /\(civ-selected\|current-age\|current-age-time\|current-score\|doctrine\|enemy-buildings-in-town\|enemy-captured-relics\|goal\|player-number\|random-number\|shared-goal\|stance-toward\|strategic-number\|town-under-attack\)/
syn match perOpponentFacts /\(players-building-count\|players-building-type-count\|players-civ\|players-civilian-population\|players-current-age\|players-current-age-time\|players-military-population\|players-population\|players-score\|players-stance\|players-unit-count\|players-unit-type-count\)/
syn match perCheatingFacts /\(cc-players-building-count\|cc-players-building-type-count\|cc-players-unit-count\|cc-players-unit-type-count\)/

"" Actions
syn match perInputOutputActions /\(chat-local\|chat-local-using-id\|chat-local-using-range\|chat-local-to-self\|chat-to-all\|chat-to-all-using-id\|chat-to-all-using-range\|chat-to-allies\|chat-to-allies-using-id\|chat-to-allies-using-range\|chat-to-enemies\|chat-to-enemies-using-id\|chat-to-enemies-using-range\|chat-to-player\|chat-to-player-using-id\|chat-to-player-using-range\|chat-trace\|log\|log-trace\|taunt\|taunt-using-range\)/
syn match perRuleControlActions /\(disable-self\)/
syn match perEventActions /\(acknowledge-event\|acknowledge-taunt\|disable-timer\|enable-timer\|set-signal\)/
syn match perCommodityTradeActions /\(buy-commodity\|sell-commodity\)/
syn match perTributeActions /\(clear-tribute-memory\|tribute-to-player\)/
syn match perEscrowActions /\(release-escrow\|set-escrow-percentage\)/
syn match perRegicideActions /spy/
syn match perCheatingActions /\(cc-add-resource\|Other Actions\|do-nothing\|attack-now\|build\|build-forward\|build-gate\|build-wall\|delete-building\|delete-unit\|enable-wall-placement\|generate-random-number\|research\|resign\|set-difficulty-parameter\|set-doctrine\|set-goal\|set-shared-goal\|set-stance\|set-strategic-number\|train\)/

syn keyword perDefine defrule defconst
syn match perOperator /[><=]/
syn match perOperator /[><!]=/
syn match perArrow /=>/
syn match perBracket /[()]/
syn match perFullOperator /\(equal\|greater-than\|less-than\|not-equal\)/
syn match perComment /;.*$/

hi link perNumber				Number
hi link perString				String
" facts
hi link perConstantFacts			Constant	
hi link perEventDetectionFacts			Function	
hi link perGameFacts				Function	
hi link perCommodityTradeFacts			Function	
hi link perTributeDetectionFacts		Function	
hi link perEscrowFacts				Function	
hi link perComputerPlayerObjectCountFacts	Function	
hi link perComputerPlayerResourceFacts		Function	
hi link perRegicideFacts			Function	
hi link perComputerPlayerAvailabilityFacts	Function	
hi link perComputerPlayerMiscellaneousFacts	Function	
hi link perOpponentFacts			Function	
hi link perCheatingFacts			Function
"  actions
hi link perInputOutputActions			Type
hi link perRuleControlActions			Type
hi link perEventActions				Type
hi link perCommodityTradeActions		Type
hi link perTributeActions			Type	
hi link perEscrowActions			Type
hi link perRegicideActions			Type
hi link perCheatingActions			Type

hi link perDefine				Define
hi link perArrow				Identifier	
hi link perOperator				Operator
hi link perFullOperator				Operator
hi link perBracket				Keyword	
hi link perComment				Comment

let b:current_syntax = "per"
