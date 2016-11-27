# Hooks

- hooks: take some arguments and return no value
- filters: take a value and return it 

## Available Hooks

#### anki.cards
- odueInvalid

#### anki.collection
- remNotes

#### anki.decks
- newDeck

#### anki.exporting
- exportedMediaFiles
- exportersList

#### anki.find
- search

#### anki.models
- newModel

#### anki.sched
- leech

#### anki.sync
- sync
- syncMsg

#### anki.tags
- newTag

#### aqt.addcards
- AddCards.onHistory

#### aqt.browser
- browser.setupMenus

#### aqt.deckbrowser
- showDeckOptions

#### aqt.editor
- editTimer
- editFocusGained
- tagsUpdated
- EditorWebView.contextMenuEvent

#### aqt.main
- profileLoaded
- uploadProfile
- beforeStateChange
- afterStateChange
- colLoading
- noteChanged
- reset
- undoState

#### aqt.modelchoooser
- currentModelChanged

#### reviewer
- reviewCleanup
- showQuestion
- showAnswer
- Reviewer.contextMenuEvent

#### aqt.sync
- httpSend
- httpRecv

#### aqt.webview
- AnkiWebView.contextMenuEvent

## Available Filters

#### anki.collection
- modSchema
- mungeFields
- mungeQA

#### anki.template
- fmod_*

#### aqt.editor
- setupEditorShortcuts
- editorFocusLost

