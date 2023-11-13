/// <reference types="cypress" />

import 'cypress-file-upload';
import * as path from 'path';

describe('Wizard loads Croissant without Error', () => {
  it('should allow uploading existing croissant files', () => {
    cy.visit('http://localhost:8501')
    cy.get('button').contains('Load').click()

    cy.fixture('titanic.json').then((fileContent) => {
      const file = {
        fileContent,
        fileName: 'titanic.json', mimeType: 'text/json',
      }
      cy.get(
        "[data-testid='stFileUploadDropzone']",
      ).attachFile(file, {
        force: true,
        subjectType: "drag-n-drop",
        events: ["dragenter", "drop"],
      })
    })

    cy.get('[data-testid="stMarkdownContainer"]').contains('Metadata').click()
    cy.get('input[aria-label="Name:red[*]"]').should('have.value', 'Titanic')
    
  })
  it('should download as json', () => {
    cy.visit('http://localhost:8501')
    cy.get('button').contains('Load').click()

    cy.fixture('titanic.json').then((fileContent) => {
      const file = {
        fileContent,
        fileName: 'titanic.json', mimeType: 'text/json',
      }
      cy.get(
        "[data-testid='stFileUploadDropzone']",
      ).attachFile(file, {
        force: true,
        subjectType: "drag-n-drop",
        events: ["dragenter", "drop"],
      })
    })
    
    cy.get('[data-testid="stException"]').should('not.exist')

    cy.get('button').contains('Save').click()
    cy.fixture('titanic.json').then((fileContent) => {
      const downloadsFolder = Cypress.config("downloadsFolder");
      cy.readFile(path.join(downloadsFolder, "croissant.json"))
      .should('eq', fileContent)
    })
  })
})